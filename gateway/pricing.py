PRICING_VERSION = "starter-2026-09-28"

PRICES = {
    "mock-fast": {"input_per_1k": 0.001, "output_per_1k": 0.002},
    "mock-strong": {"input_per_1k": 0.01, "output_per_1k": 0.03},
}


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in PRICES:
        raise ValueError(f"Unknown model pricing: {model}")

    price = PRICES[model]
    return (input_tokens / 1000 * price["input_per_1k"]) + (
        output_tokens / 1000 * price["output_per_1k"]
    )
