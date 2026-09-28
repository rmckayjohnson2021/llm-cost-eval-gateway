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
    provider: str = "mock"
    model: str | None = None
    text: str = ""
    route_reason: str
    attempts: int = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    reserved_cost_usd: float = 0.0
    estimated_cost_usd: float = 0.0
    latency_ms: int = 0
    error_type: str | None = None


class UsageRecord(BaseModel):
    run_id: str
    app_name: str
    workflow_version: str
    simulated_team_id: str
    provider: str
    model: str | None
    route: Route
    status: Status
    attempts: int
    input_tokens: int | None = None
    output_tokens: int | None = None
    reserved_cost_usd: float
    estimated_cost_usd: float
    pricing_version: str
    latency_ms: int
    error_type: str | None = None


class RoutingDecision(BaseModel):
    route: Route
    model: str | None
    reason: str
