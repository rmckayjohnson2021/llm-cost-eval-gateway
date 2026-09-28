from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, status

from gateway.executor import execute
from gateway.ledger import fetch_usage
from gateway.reporting import render_usage_summary_report, summarize_usage
from gateway.schemas import ModelRequest, ModelResponse
from gateway.settings import api_key, ledger_path

app = FastAPI(
    title="LLM Cost and Evaluation Gateway",
    version="0.1.0",
    summary="Reusable model execution gateway with routing, budget checks, retries, and usage reporting.",
)


def require_api_key(x_gateway_api_key: str | None = Header(default=None)) -> None:
    if x_gateway_api_key != api_key():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid gateway API key.",
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/execute", response_model=ModelResponse, dependencies=[Depends(require_api_key)])
def execute_request(request: ModelRequest) -> ModelResponse:
    return execute(request, ledger_path=ledger_path())


@app.get("/v1/usage", dependencies=[Depends(require_api_key)])
def usage() -> list[dict[str, Any]]:
    return fetch_usage(ledger_path())


@app.get("/v1/usage/summary", dependencies=[Depends(require_api_key)])
def usage_summary() -> dict[str, Any]:
    rows = fetch_usage(ledger_path())
    return {
        "total_rows": len(rows),
        "by_route": summarize_usage(rows, "route"),
        "by_model": summarize_usage(rows, "model"),
        "by_status": summarize_usage(rows, "status"),
    }


@app.get("/v1/usage/summary.md", response_model=None, dependencies=[Depends(require_api_key)])
def usage_summary_markdown() -> str:
    return render_usage_summary_report(fetch_usage(ledger_path()))
