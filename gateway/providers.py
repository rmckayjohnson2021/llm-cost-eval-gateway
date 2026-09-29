import json
import os
from dataclasses import dataclass
from typing import Any, Protocol

from dotenv import load_dotenv

load_dotenv()

PLACEHOLDER_VALUES = {"", "replace_me", "your_openai_api_key_here"}
OPENAI_MODEL_ALIASES = {
    "openai-fast": "DEFAULT_FAST_MODEL",
    "openai-strong": "DEFAULT_STRONG_MODEL",
}


@dataclass
class ProviderResult:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    error_type: str | None = None


class Provider(Protocol):
    name: str

    def complete(self, prompt: str, model: str, max_output_tokens: int) -> ProviderResult:
        pass


class MockProvider:
    name = "mock"

    def __init__(self, mode: str = "success") -> None:
        self.mode = mode
        self.calls = 0

    def complete(self, prompt: str, model: str, max_output_tokens: int) -> ProviderResult:
        self.calls += 1

        if self.mode == "timeout":
            return ProviderResult(text="", error_type="timeout")
        if self.mode == "rate_limit":
            return ProviderResult(text="", error_type="rate_limit")
        if self.mode == "outage":
            return ProviderResult(text="", error_type="provider_outage")
        if self.mode == "invalid":
            return ProviderResult(text="not-json", input_tokens=10, output_tokens=3)

        return ProviderResult(
            text=mock_response_text(prompt),
            input_tokens=max(1, len(prompt.split())),
            output_tokens=10,
        )


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or configured_api_key()

    def complete(self, prompt: str, model: str, max_output_tokens: int) -> ProviderResult:
        if self.api_key is None:
            return ProviderResult(text="", error_type="missing_api_key")

        if model.startswith("mock-"):
            return ProviderResult(text="", error_type="provider_policy_mismatch")

        resolved_model = resolve_openai_model(model)
        if resolved_model is None:
            return ProviderResult(text="", error_type="missing_model_config")

        try:
            from openai import OpenAI, OpenAIError

            client = OpenAI(api_key=self.api_key)
            response = client.responses.create(
                model=resolved_model,
                input=prompt,
                max_output_tokens=max_output_tokens,
            )
            text = extract_response_text(response)
            if not text:
                return ProviderResult(text="", error_type="empty_response")
            input_tokens, output_tokens = extract_usage(response)
            return ProviderResult(text=text, input_tokens=input_tokens, output_tokens=output_tokens)
        except ImportError:
            return ProviderResult(text="", error_type="openai_dependency_missing")
        except OpenAIError:
            return ProviderResult(text="", error_type="provider_error")
        except ValueError:
            return ProviderResult(text="", error_type="provider_error")


def configured_api_key() -> str | None:
    value = os.getenv("OPENAI_API_KEY", "").strip()
    return None if value in PLACEHOLDER_VALUES else value


def mock_response_text(prompt: str) -> str:
    lower_prompt = prompt.lower()
    if "incidentanalysis" not in lower_prompt and "review_status" not in lower_prompt:
        return "mock response"

    category = "failed_import"
    severity = "sev3"
    source_runbook = "failed_import.md"
    recommendation = "Validate the source file, compare expected row counts, correct the import issue, and rerun the job."

    if any(term in lower_prompt for term in ("schema", "column", "field", "loyalty_tier")):
        category = "schema_change"
        severity = "sev2"
        source_runbook = "schema_change.md"
        recommendation = (
            "Validate whether the column change is expected, update the parser or mapping, "
            "and rerun the import after review."
        )
    elif any(term in lower_prompt for term in ("duplicate", "replay", "upsert")):
        category = "duplicate_records"
        severity = "sev3"
        source_runbook = "duplicate_records.md"
        recommendation = "Identify duplicate keys, isolate the affected window, and rerun with corrected deduplication logic."
    elif any(term in lower_prompt for term in ("dashboard", "refresh", "stale", "bi")):
        category = "stale_dashboard"
        severity = "sev3"
        source_runbook = "stale_dashboard.md"
        recommendation = "Confirm warehouse freshness, rerun the BI refresh, and notify stakeholders if stale data persists."

    return json.dumps(
        {
            "category": category,
            "severity": severity,
            "summary": f"Mock gateway analysis classified the incident as {category}.",
            "evidence": ["Gateway mock provider returned structured output for local integration testing."],
            "recommendation": recommendation,
            "source_runbooks": [source_runbook],
            "route": "strong_model" if severity in {"sev1", "sev2"} else "fast_model",
            "route_reason": "Local gateway mock response for integration testing.",
            "review_status": "approved",
            "workflow_version": "v1.0.0",
        }
    )


def configured_provider_name() -> str:
    value = os.getenv("GATEWAY_PROVIDER", "mock").strip().lower()
    return value if value in {"mock", "openai"} else "mock"


def resolve_openai_model(model: str) -> str | None:
    env_name = OPENAI_MODEL_ALIASES.get(model)
    if env_name is None:
        return model

    value = os.getenv(env_name, "").strip()
    return None if value in PLACEHOLDER_VALUES else value


def create_provider_from_env() -> Provider:
    if configured_provider_name() == "openai":
        return OpenAIProvider()
    return MockProvider()


def extract_response_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    chunks: list[str] = []
    for item in getattr(response, "output", []) or []:
        for content in getattr(item, "content", []) or []:
            if isinstance(content, dict):
                text = content.get("text") or content.get("output_text")
            else:
                text = getattr(content, "text", None)
            if text:
                chunks.append(text)
    return "\n".join(chunks)


def extract_usage(response: Any) -> tuple[int | None, int | None]:
    usage = getattr(response, "usage", None)
    if usage is None:
        return None, None
    return getattr(usage, "input_tokens", None), getattr(usage, "output_tokens", None)
