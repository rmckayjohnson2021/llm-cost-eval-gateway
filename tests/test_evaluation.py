from gateway.evaluation import summarize_results


def test_summarize_results_includes_cost_latency_and_routing_metrics():
    summary = summarize_results(
        [
            {
                "acceptable": True,
                "status": "success",
                "estimated_cost_usd": 0.10,
                "latency_ms": 100,
            },
            {
                "acceptable": False,
                "status": "human_review",
                "estimated_cost_usd": 0.0,
                "latency_ms": 10,
            },
            {
                "acceptable": False,
                "status": "blocked",
                "estimated_cost_usd": 0.20,
                "latency_ms": 5,
            },
        ]
    )

    assert summary["total_cases"] == 3
    assert summary["acceptable_results"] == 1
    assert summary["human_review_rate"] == 1 / 3
    assert summary["blocked_rate"] == 1 / 3
    assert summary["total_estimated_cost_usd"] == 0.30
    assert summary["median_latency_ms"] == 10
    assert summary["slowest_latency_ms"] == 100
    assert summary["cost_per_acceptable_result"] == 0.30
