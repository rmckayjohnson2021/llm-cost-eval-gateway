from fastapi.testclient import TestClient

from gateway.api import app

AUTH_HEADERS = {"X-Gateway-API-Key": "test-key"}


def test_health_endpoint():
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_v1_endpoints_require_api_key(monkeypatch):
    monkeypatch.setenv("GATEWAY_API_KEY", "test-key")
    client = TestClient(app)

    response = client.get("/v1/usage")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid gateway API key."


def test_execute_endpoint_records_usage(monkeypatch, tmp_path):
    ledger_path = tmp_path / "api-ledger.db"
    monkeypatch.setenv("GATEWAY_LEDGER_PATH", str(ledger_path))
    monkeypatch.setenv("GATEWAY_API_KEY", "test-key")
    client = TestClient(app)

    response = client.post(
        "/v1/execute",
        headers=AUTH_HEADERS,
        json={
            "app_name": "api-test",
            "workflow_version": "v1",
            "simulated_user_id": "user-1",
            "simulated_team_id": "team-1",
            "input_text": "routine import issue",
            "route_policy": "routed",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["route"] == "fast_model"

    usage = client.get("/v1/usage", headers=AUTH_HEADERS).json()
    assert len(usage) == 1
    assert usage[0]["run_id"] == payload["run_id"]


def test_usage_summary_endpoint(monkeypatch, tmp_path):
    ledger_path = tmp_path / "api-ledger.db"
    monkeypatch.setenv("GATEWAY_LEDGER_PATH", str(ledger_path))
    monkeypatch.setenv("GATEWAY_API_KEY", "test-key")
    client = TestClient(app)

    client.post(
        "/v1/execute",
        headers=AUTH_HEADERS,
        json={
            "app_name": "api-test",
            "workflow_version": "v1",
            "simulated_user_id": "user-1",
            "simulated_team_id": "team-1",
            "input_text": "unclear ambiguous dashboard issue",
            "route_policy": "routed",
        },
    )

    summary = client.get("/v1/usage/summary", headers=AUTH_HEADERS).json()
    assert summary["total_rows"] == 1
    assert summary["by_status"][0]["status"] == "human_review"

    markdown = client.get("/v1/usage/summary.md", headers=AUTH_HEADERS)
    assert markdown.status_code == 200
    assert "# Usage Ledger Summary" in markdown.text
