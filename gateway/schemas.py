from typing import Any, Literal

from pydantic import BaseModel, Field

Route = Literal["fast_model", "strong_model", "human_review"]
Status = Literal["success", "blocked", "failed", "human_review"]


class ModelRequest(BaseModel):
    app_name: str
    workflow_version: str
    simulated_user_id: str
    simulated_team_id: str
    input_text: str
    max_input_tokens: int = 4000
    max_output_tokens: int = 1000
    route_policy: str = "rules_v1"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ModelResponse(BaseModel):
    run_id: str
    route: Route
    status: Status
    text: str = ""
    route_reason: str
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    error_type: str | None = None


class UsageRecord(BaseModel):
    run_id: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float
    pricing_version: str


class RoutingDecision(BaseModel):
    route: Route
    model: str | None
    reason: str
