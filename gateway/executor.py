import time
from uuid import uuid4

from gateway.budgets import BudgetState
from gateway.ledger import record_usage
from gateway.pricing import PRICING_VERSION, estimate_cost_usd
from gateway.providers import Provider, create_provider_from_env
from gateway.retries import is_retryable
from gateway.routing import choose_route
from gateway.schemas import ModelRequest, ModelResponse, UsageRecord


def _record(request: ModelRequest, response: ModelResponse, ledger_path: str | None) -> None:
    if ledger_path is None:
        return

    record_usage(
        UsageRecord(
            run_id=response.run_id,
            incident_type=incident_type_from_metadata(request),
            app_name=request.app_name,
            workflow_version=request.workflow_version,
            simulated_team_id=request.simulated_team_id,
            provider=response.provider,
            model=response.model,
            route=response.route,
            status=response.status,
            attempts=response.attempts,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            reserved_cost_usd=response.reserved_cost_usd,
            estimated_cost_usd=response.estimated_cost_usd,
            pricing_version=PRICING_VERSION,
            latency_ms=response.latency_ms,
            error_type=response.error_type,
        ),
        path=ledger_path,
    )


def incident_type_from_metadata(request: ModelRequest) -> str | None:
    for key in ("incident_type", "category", "case_type"):
        value = str(request.metadata.get(key, "")).strip()
        if value:
            return value
    return None


def execute(
    request: ModelRequest,
    provider: Provider | None = None,
    budget: BudgetState | None = None,
    *,
    ledger_path: str | None = None,
    max_attempts: int = 2,
) -> ModelResponse:
    run_id = str(uuid4())
    start = time.perf_counter()
    provider = provider or create_provider_from_env()
    provider_name = getattr(provider, "name", "unknown")
    budget = budget or BudgetState(limit_usd=20.0)
    decision = choose_route(request)

    if decision.route == "human_review" or decision.model is None:
        response = ModelResponse(
            run_id=run_id,
            route="human_review",
            status="human_review",
            provider=provider_name,
            route_reason=decision.reason,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
        _record(request, response, ledger_path)
        return response

    reserved = estimate_cost_usd(
        decision.model,
        request.max_input_tokens,
        request.max_output_tokens,
    )

    if not budget.reserve(reserved):
        response = ModelResponse(
            run_id=run_id,
            route=decision.route,
            status="blocked",
            provider=provider_name,
            model=decision.model,
            route_reason="Budget reservation failed before provider call.",
            reserved_cost_usd=reserved,
            estimated_cost_usd=reserved,
            latency_ms=int((time.perf_counter() - start) * 1000),
            error_type="budget_exceeded",
        )
        _record(request, response, ledger_path)
        return response

    attempts = 0
    result = None
    for attempt in range(1, max(1, max_attempts) + 1):
        attempts = attempt
        result = provider.complete(request.input_text, decision.model, request.max_output_tokens)
        if not is_retryable(result.error_type):
            break

    if result is None:
        raise RuntimeError("Provider execution did not run.")

    status = "failed" if result.error_type else "success"
    actual_cost = 0.0
    if result.input_tokens is not None and result.output_tokens is not None:
        actual_cost = estimate_cost_usd(decision.model, result.input_tokens, result.output_tokens)

    if status == "success":
        budget.commit(reserved, actual_cost)
    else:
        budget.release(reserved)

    response = ModelResponse(
        run_id=run_id,
        route=decision.route,
        status=status,
        provider=provider_name,
        model=decision.model,
        text=result.text,
        route_reason=decision.reason,
        attempts=attempts,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        reserved_cost_usd=reserved,
        estimated_cost_usd=actual_cost,
        latency_ms=int((time.perf_counter() - start) * 1000),
        error_type=result.error_type,
    )
    _record(request, response, ledger_path)
    return response
