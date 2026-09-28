from pathlib import Path

from streamlit.testing.v1 import AppTest

from gateway.ledger import record_usage
from gateway.pricing import PRICING_VERSION
from gateway.schemas import UsageRecord

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_renders_empty_state(monkeypatch, tmp_path):
    monkeypatch.setenv("GATEWAY_LEDGER_PATH", str(tmp_path / "empty.db"))

    app = AppTest.from_file(PROJECT_ROOT / "dashboard_app.py").run(timeout=30)

    assert not app.exception
    assert any(title.value == "CostOps Gateway" for title in app.title)
    assert any("No usage rows yet" in subheader.value for subheader in app.subheader)


def test_dashboard_renders_usage_metrics(monkeypatch, tmp_path):
    ledger_path = tmp_path / "usage.db"
    monkeypatch.setenv("GATEWAY_LEDGER_PATH", str(ledger_path))
    record_usage(
        UsageRecord(
            run_id="run-1",
            incident_type="schema_change",
            app_name="test",
            workflow_version="v1",
            simulated_team_id="team-1",
            provider="mock",
            model="mock-fast",
            route="fast_model",
            status="success",
            attempts=1,
            input_tokens=10,
            output_tokens=5,
            reserved_cost_usd=0.006,
            estimated_cost_usd=0.001,
            pricing_version=PRICING_VERSION,
            latency_ms=12,
        ),
        path=str(ledger_path),
    )

    app = AppTest.from_file(PROJECT_ROOT / "dashboard_app.py").run(timeout=30)

    assert not app.exception
    assert any(metric.label == "Calls" and metric.value == "1" for metric in app.metric)
    assert any(metric.label == "Estimated cost" and metric.value == "$0.001000" for metric in app.metric)
    assert any(metric.label == "Routing savings" for metric in app.metric)
    assert any("Cost by incident type" in subheader.value for subheader in app.subheader)
