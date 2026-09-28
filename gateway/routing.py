from gateway.schemas import ModelRequest, RoutingDecision


def choose_route(request: ModelRequest) -> RoutingDecision:
    text = request.input_text.lower()

    if "ambiguous" in text or "unclear" in text:
        return RoutingDecision(route="human_review", model=None, reason="Ambiguous or unclear evidence.")

    if "sev1" in text or "outage" in text:
        return RoutingDecision(route="strong_model", model="mock-strong", reason="High-impact language detected.")

    return RoutingDecision(route="fast_model", model="mock-fast", reason="Routine request with no high-risk signals.")
