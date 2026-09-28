import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gateway.budgets import BudgetState
from gateway.executor import execute
from gateway.ledger import fetch_usage
from gateway.schemas import ModelRequest, ModelResponse

REPORT_PATH = Path("reports/gateway_demo_report.md")
LEDGER_PATH = "reports/gateway_demo_ledger.db"
POLICIES = ["fast_only", "strong_only", "routed"]


def demo_request(case_id: str, input_text: str, route_policy: str) -> ModelRequest:
    return ModelRequest(
        app_name="runbookops-ai",
        workflow_version="v1",
        simulated_user_id="demo-user",
        simulated_team_id="ops-team",
        input_text=input_text,
        route_policy=route_policy,
        metadata={"case_id": case_id},
    )


def summarize_policy(responses: list[ModelResponse]) -> dict[str, int | float]:
    routes = Counter(response.route for response in responses)
    statuses = Counter(response.status for response in responses)
    return {
        "cases": len(responses),
        "fast": routes["fast_model"],
        "strong": routes["strong_model"],
        "human_review": routes["human_review"],
        "blocked": statuses["blocked"],
        "failed": statuses["failed"],
        "estimated_cost_usd": sum(response.estimated_cost_usd for response in responses),
    }


def main() -> None:
    ledger_file = Path(LEDGER_PATH)
    if ledger_file.exists():
        ledger_file.unlink()

    cases = [
        ("case-routine", "Routine import issue with bounded impact."),
        ("case-sev1", "SEV1 outage language detected for executive dashboard workflow."),
        ("case-review", "Unclear ambiguous incident with conflicting service signals."),
    ]
    budget = BudgetState(limit_usd=0.25)
    responses_by_policy: dict[str, list[ModelResponse]] = {}

    for policy in POLICIES:
        responses_by_policy[policy] = [
            execute(
                demo_request(case_id, input_text, policy),
                budget=budget,
                ledger_path=LEDGER_PATH,
            )
            for case_id, input_text in cases
        ]

    rows = fetch_usage(LEDGER_PATH)

    detail_rows = []
    for policy, responses in responses_by_policy.items():
        for (case_id, _input_text), response in zip(cases, responses, strict=True):
            detail_rows.append(
                f"| {policy} | {case_id} | {response.route} | {response.status} | "
                f"{response.model or '-'} | {response.attempts} | "
                f"${response.reserved_cost_usd:.6f} | ${response.estimated_cost_usd:.6f} | "
                f"{response.route_reason} |"
            )

    summary_rows = []
    for policy, responses in responses_by_policy.items():
        summary = summarize_policy(responses)
        summary_rows.append(
            f"| {policy} | {summary['cases']} | {summary['fast']} | {summary['strong']} | "
            f"{summary['human_review']} | {summary['blocked']} | {summary['failed']} | "
            f"${summary['estimated_cost_usd']:.6f} |"
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# Gateway Demo Report",
                "",
                "This report runs the same synthetic requests through three routing policies: `fast_only`, `strong_only`, and `routed`.",
                "",
                "## Policy Comparison",
                "",
                "| Policy | Cases | Fast | Strong | Human Review | Blocked | Failed | Estimated Cost |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
                *summary_rows,
                "",
                "## Request-Level Results",
                "",
                "| Policy | Case | Route | Status | Model | Attempts | Reserved | Estimated | Reason |",
                "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- |",
                *detail_rows,
                "",
                "## Budget State",
                "",
                f"- Limit: `${budget.limit_usd:.2f}`",
                f"- Spent: `${budget.spent_usd:.6f}`",
                f"- Reserved: `${budget.reserved_usd:.6f}`",
                f"- Available: `${budget.available_usd:.6f}`",
                "",
                "## Ledger",
                "",
                f"- Rows written: `{len(rows)}`",
                f"- Ledger path: `{LEDGER_PATH}`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
