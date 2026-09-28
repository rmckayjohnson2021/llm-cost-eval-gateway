from collections import defaultdict
from statistics import median
from typing import Any

from gateway.pricing import estimate_cost_usd

STRONG_BASELINE_BY_MODEL = {
    "mock-fast": "mock-strong",
    "mock-strong": "mock-strong",
    "openai-fast": "openai-strong",
    "openai-strong": "openai-strong",
}


def summarize_usage(rows: list[dict[str, Any]], group_by: str) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        groups[str(row.get(group_by) or "-")].append(row)

    summaries = []
    for key, items in sorted(groups.items()):
        costs = [float(item.get("estimated_cost_usd") or 0.0) for item in items]
        latencies = [int(item.get("latency_ms") or 0) for item in items]
        summaries.append(
            {
                group_by: key,
                "calls": len(items),
                "estimated_cost_usd": round(sum(costs), 10),
                "median_latency_ms": median(latencies) if latencies else 0,
                "failed": sum(1 for item in items if item.get("status") == "failed"),
                "blocked": sum(1 for item in items if item.get("status") == "blocked"),
                "human_review": sum(1 for item in items if item.get("status") == "human_review"),
            }
        )
    return summaries


def format_latency(value: float) -> str:
    return f"{value:.0f}" if float(value).is_integer() else f"{value:.1f}"


def estimate_strong_baseline_cost(row: dict[str, Any]) -> float:
    model = row.get("model")
    baseline_model = STRONG_BASELINE_BY_MODEL.get(str(model))
    input_tokens = row.get("input_tokens")
    output_tokens = row.get("output_tokens")
    if baseline_model is None or input_tokens is None or output_tokens is None:
        return 0.0
    return estimate_cost_usd(baseline_model, int(input_tokens), int(output_tokens))


def summarize_optimization_savings(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    actual_cost = round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows), 10)
    strong_baseline_cost = round(sum(estimate_strong_baseline_cost(row) for row in rows), 10)
    estimated_savings = round(max(0.0, strong_baseline_cost - actual_cost), 10)
    eligible_rows = sum(1 for row in rows if estimate_strong_baseline_cost(row) > 0)
    optimized_rows = sum(
        1
        for row in rows
        if estimate_strong_baseline_cost(row) > float(row.get("estimated_cost_usd") or 0.0)
    )
    return {
        "actual_cost_usd": actual_cost,
        "strong_baseline_cost_usd": strong_baseline_cost,
        "estimated_savings_usd": estimated_savings,
        "savings_rate": estimated_savings / strong_baseline_cost if strong_baseline_cost else 0,
        "eligible_rows": eligible_rows,
        "optimized_rows": optimized_rows,
    }


def render_usage_summary_report(rows: list[dict[str, Any]]) -> str:
    total_cost = round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows), 10)
    savings = summarize_optimization_savings(rows)
    lines = [
        "# Usage Ledger Summary",
        "",
        f"- Total rows: `{len(rows)}`",
        f"- Total estimated cost: `${total_cost:.6f}`",
        f"- Strong-only baseline cost: `${savings['strong_baseline_cost_usd']:.6f}`",
        f"- Estimated routing savings: `${savings['estimated_savings_usd']:.6f}`",
        f"- Savings rate: `{savings['savings_rate']:.1%}`",
        "",
    ]

    for group_by, label in (
        ("route", "By Route"),
        ("model", "By Model"),
        ("incident_type", "By Incident Type"),
        ("status", "By Status"),
    ):
        lines.extend(
            [
                f"## {label}",
                "",
                f"| {group_by.title()} | Calls | Estimated Cost | Median Latency | Failed | Blocked | Human Review |",
                "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for summary in summarize_usage(rows, group_by):
            lines.append(
                f"| {summary[group_by]} | {summary['calls']} | "
                f"${summary['estimated_cost_usd']:.6f} | {format_latency(summary['median_latency_ms'])} ms | "
                f"{summary['failed']} | {summary['blocked']} | {summary['human_review']} |"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
