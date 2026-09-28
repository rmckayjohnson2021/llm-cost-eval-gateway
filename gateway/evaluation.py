from statistics import median
from typing import Any


def summarize_results(results: list[dict[str, Any]]) -> dict[str, float | int]:
    total = len(results)
    acceptable = sum(1 for item in results if item.get("acceptable"))
    human_review = sum(1 for item in results if item.get("status") == "human_review")
    failed = sum(1 for item in results if item.get("status") == "failed")
    blocked = sum(1 for item in results if item.get("status") == "blocked")
    costs = [float(item.get("estimated_cost_usd", 0.0)) for item in results]
    latencies = [int(item.get("latency_ms", 0)) for item in results]
    total_cost = round(sum(costs), 10)

    return {
        "total_cases": total,
        "acceptable_results": acceptable,
        "acceptable_rate": acceptable / total if total else 0,
        "human_review_rate": human_review / total if total else 0,
        "failed_rate": failed / total if total else 0,
        "blocked_rate": blocked / total if total else 0,
        "total_estimated_cost_usd": total_cost,
        "median_latency_ms": median(latencies) if latencies else 0,
        "slowest_latency_ms": max(latencies) if latencies else 0,
        "cost_per_acceptable_result": round(total_cost / acceptable, 10) if acceptable else 0,
    }
