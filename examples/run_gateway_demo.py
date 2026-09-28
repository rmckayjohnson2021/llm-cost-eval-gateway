import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gateway.budgets import BudgetState
from gateway.executor import execute
from gateway.ledger import fetch_usage
from gateway.schemas import ModelRequest

REPORT_PATH = Path("reports/gateway_demo_report.md")
LEDGER_PATH = "reports/gateway_demo_ledger.db"


def demo_request(case_id: str, input_text: str) -> ModelRequest:
    return ModelRequest(
        app_name="runbookops-ai",
        workflow_version="v1",
        simulated_user_id="demo-user",
        simulated_team_id="ops-team",
        input_text=input_text,
        metadata={"case_id": case_id},
    )


def main() -> None:
    budget = BudgetState(limit_usd=0.25)
    requests = [
        demo_request("case-routine", "Routine import issue with bounded impact."),
        demo_request("case-sev1", "SEV1 outage language detected for executive dashboard workflow."),
        demo_request("case-review", "Unclear ambiguous incident with conflicting service signals."),
    ]

    responses = [
        execute(request, budget=budget, ledger_path=LEDGER_PATH)
        for request in requests
    ]
    rows = fetch_usage(LEDGER_PATH)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        "\n".join(
            [
                "# Gateway Demo Report",
                "",
                "| Case | Route | Status | Model | Attempts | Reserved | Estimated | Reason |",
                "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
                *[
                    (
                        f"| {request.metadata['case_id']} | {response.route} | {response.status} | "
                        f"{response.model or '-'} | {response.attempts} | "
                        f"${response.reserved_cost_usd:.6f} | ${response.estimated_cost_usd:.6f} | "
                        f"{response.route_reason} |"
                    )
                    for request, response in zip(requests, responses, strict=True)
                ],
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
        ),
        encoding="utf-8",
    )
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
