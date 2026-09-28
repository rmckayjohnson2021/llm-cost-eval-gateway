from dataclasses import dataclass


@dataclass
class ProviderResult:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    error_type: str | None = None


class MockProvider:
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
            text="mock response",
            input_tokens=max(1, len(prompt.split())),
            output_tokens=10,
        )
