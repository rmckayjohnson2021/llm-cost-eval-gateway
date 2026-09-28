import time
from uuid import uuid4

from gateway.budgets import BudgetState
from gateway.pricing import estimate_cost_usd
from gateway.providers import MockProvider
from gateway.routing import choose_route
from gateway.schemas import ModelRequest, ModelResponse


def execute(
    request: ModelRequest,
    provider: MockProvider | None = None,
    budget: BudgetState | None = None,
) -> ModelResponse:
    run_id = str(uuid4())
    start = time.perf_counter()
    provider = provider or MockProvider()
    budget = budget or BudgetState(limit_usd=20.0)
    decision = choose_route(request)

    if decision.route == "human_review" or decision.model is None:
        return ModelResponse(
            run_id=run_id,
            route="human_review",
            status="human_review",
            route_reason=decision.reason,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )

    estimated = estimate_cost_usd(
        decision.model,
        request.max_input_tokens,
        request.max_output_tokens,
    )

    if not budget.reserve(estimated):
        return ModelResponse(
            run_id=run_id,
            route=decision.route,
            status="blocked",
            route_reason="Budget reservation failed before provider call.",
            estimated_cost_usd=estimated,
            latency_ms=int((time.perf_counter() - start) * 1000),
            error_type="budget_exceeded",
        )

    result = provider.complete(request.input_text, decision.model, request.max_output_tokens)
    status = "failed" if result.error_type else "success"

    return ModelResponse(
        run_id=run_id,
        route=decision.route,
        status=status,
        text=result.text,
        route_reason=decision.reason,
        estimated_cost_usd=estimated,
        latency_ms=int((time.perf_counter() - start) * 1000),
        error_type=result.error_type,
    )
