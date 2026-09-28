from gateway.budgets import BudgetState
from gateway.executor import execute
from gateway.ledger import fetch_usage
from gateway.providers import MockProvider
from gateway.schemas import ModelRequest


def make_request(input_text: str = "routine import issue") -> ModelRequest:
    return ModelRequest(
        app_name="test",
        workflow_version="v1",
        simulated_user_id="user-1",
        simulated_team_id="team-1",
        input_text=input_text,
    )


def test_execute_success():
    response = execute(make_request())

    assert response.status == "success"
    assert response.route == "fast_model"
    assert response.model == "mock-fast"
    assert response.input_tokens is not None
    assert response.output_tokens is not None


def test_execute_routes_ambiguous_requests_to_human_review():
    response = execute(make_request("unclear ambiguous issue across dashboards"))

    assert response.status == "human_review"
    assert response.route == "human_review"
    assert response.attempts == 0


def test_execute_blocks_before_provider_call_when_budget_is_exceeded():
    provider = MockProvider()
    budget = BudgetState(limit_usd=0.00001)

    response = execute(make_request("sev1 outage"), provider=provider, budget=budget)

    assert response.status == "blocked"
    assert response.error_type == "budget_exceeded"
    assert provider.calls == 0


def test_execute_releases_budget_after_retryable_provider_failure():
    provider = MockProvider(mode="timeout")
    budget = BudgetState(limit_usd=1.0)

    response = execute(make_request(), provider=provider, budget=budget, max_attempts=2)

    assert response.status == "failed"
    assert response.error_type == "timeout"
    assert response.attempts == 2
    assert provider.calls == 2
    assert budget.reserved_usd == 0.0
    assert budget.spent_usd == 0.0


def test_execute_records_usage_to_ledger(tmp_path):
    ledger_path = tmp_path / "usage.db"

    response = execute(make_request(), ledger_path=str(ledger_path))
    rows = fetch_usage(str(ledger_path))

    assert response.status == "success"
    assert len(rows) == 1
    assert rows[0]["run_id"] == response.run_id
    assert rows[0]["status"] == "success"
    assert rows[0]["model"] == "mock-fast"
