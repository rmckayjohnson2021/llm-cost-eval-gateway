from gateway.budgets import BudgetState


def test_budget_blocks_when_limit_exceeded():
    budget = BudgetState(limit_usd=1.0)
    assert budget.reserve(0.75)
    assert not budget.reserve(0.50)


def test_budget_commit_moves_reserved_to_spent():
    budget = BudgetState(limit_usd=1.0)

    assert budget.reserve(0.50)
    budget.commit(reserved_usd=0.50, actual_usd=0.20)

    assert budget.reserved_usd == 0.0
    assert budget.spent_usd == 0.20
    assert budget.available_usd == 0.80


def test_budget_release_restores_available_budget():
    budget = BudgetState(limit_usd=1.0)

    assert budget.reserve(0.50)
    budget.release(0.50)

    assert budget.reserved_usd == 0.0
    assert budget.spent_usd == 0.0
    assert budget.available_usd == 1.0
