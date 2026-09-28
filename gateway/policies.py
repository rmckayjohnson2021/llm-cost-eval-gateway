from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY_PATH = PROJECT_ROOT / "examples" / "routing_policies.yaml"


class RoutingPolicy(BaseModel):
    description: str = ""
    fast_model: str
    strong_model: str
    default_route: Literal["fast_model", "strong_model"] = "fast_model"
    human_review_signals: list[str] = Field(default_factory=list)
    strong_model_signals: list[str] = Field(default_factory=list)


class RoutingPolicyCatalog(BaseModel):
    policies: dict[str, RoutingPolicy]


@lru_cache
def load_policy_catalog(path: str | None = None) -> RoutingPolicyCatalog:
    policy_path = Path(path) if path else DEFAULT_POLICY_PATH
    payload = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    return RoutingPolicyCatalog.model_validate(payload)


def get_policy(name: str, path: str | None = None) -> RoutingPolicy:
    catalog = load_policy_catalog(path)
    if name not in catalog.policies:
        available = ", ".join(sorted(catalog.policies))
        raise ValueError(f"Unknown route policy '{name}'. Available policies: {available}")
    return catalog.policies[name]


def contains_signal(text: str, signals: list[str]) -> str | None:
    for signal in signals:
        if signal.lower() in text:
            return signal
    return None
