from collections import defaultdict
from statistics import median
from typing import Any


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


def render_usage_summary_report(rows: list[dict[str, Any]]) -> str:
    total_cost = round(sum(float(row.get("estimated_cost_usd") or 0.0) for row in rows), 10)
    lines = [
        "# Usage Ledger Summary",
        "",
        f"- Total rows: `{len(rows)}`",
        f"- Total estimated cost: `${total_cost:.6f}`",
        "",
    ]

    for group_by, label in (("route", "By Route"), ("model", "By Model"), ("status", "By Status")):
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
