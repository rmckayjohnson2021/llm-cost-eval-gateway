from gateway.budgets import BudgetState


def test_budget_blocks_when_limit_exceeded():
    budget = BudgetState(limit_usd=1.0)
    assert budget.reserve(0.75)
    assert not budget.reserve(0.50)
