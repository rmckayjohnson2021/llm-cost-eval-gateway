from gateway.reporting import (
    format_latency,
    render_usage_summary_report,
    summarize_usage,
)


def test_summarize_usage_groups_cost_and_counts_by_route():
    rows = [
        {"route": "fast_model", "status": "success", "estimated_cost_usd": 0.10, "latency_ms": 10},
        {"route": "fast_model", "status": "failed", "estimated_cost_usd": 0.20, "latency_ms": 20},
        {"route": "human_review", "status": "human_review", "estimated_cost_usd": 0.0, "latency_ms": 1},
    ]

    summary = summarize_usage(rows, "route")

    assert summary == [
        {
            "route": "fast_model",
            "calls": 2,
            "estimated_cost_usd": 0.30,
            "median_latency_ms": 15.0,
            "failed": 1,
            "blocked": 0,
            "human_review": 0,
        },
        {
            "route": "human_review",
            "calls": 1,
            "estimated_cost_usd": 0.0,
            "median_latency_ms": 1,
            "failed": 0,
            "blocked": 0,
            "human_review": 1,
        },
    ]


def test_render_usage_summary_report_includes_route_model_and_status_sections():
    rows = [
        {
            "route": "fast_model",
            "model": "mock-fast",
            "status": "success",
            "estimated_cost_usd": 0.10,
            "latency_ms": 10,
        }
    ]

    report = render_usage_summary_report(rows)

    assert "# Usage Ledger Summary" in report
    assert "## By Route" in report
    assert "## By Model" in report
    assert "## By Status" in report
    assert "| fast_model | 1 | $0.100000 | 10 ms | 0 | 0 | 0 |" in report


def test_format_latency_suppresses_unnecessary_decimal():
    assert format_latency(0.0) == "0"
    assert format_latency(15.5) == "15.5"
