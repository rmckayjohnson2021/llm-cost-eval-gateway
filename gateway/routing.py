from gateway.policies import contains_signal, get_policy
from gateway.schemas import ModelRequest, RoutingDecision


def choose_route(request: ModelRequest) -> RoutingDecision:
    policy = get_policy(request.route_policy)
    routing_text = str(request.metadata.get("routing_text") or request.input_text)
    text = routing_text.lower()

    review_signal = contains_signal(text, policy.human_review_signals)
    if review_signal:
        return RoutingDecision(
            route="human_review",
            model=None,
            reason=f"Policy '{request.route_policy}' matched human-review signal: {review_signal}.",
        )

    strong_signal = contains_signal(text, policy.strong_model_signals)
    if strong_signal:
        return RoutingDecision(
            route="strong_model",
            model=policy.strong_model,
            reason=f"Policy '{request.route_policy}' matched strong-model signal: {strong_signal}.",
        )

    if policy.default_route == "strong_model":
        return RoutingDecision(
            route="strong_model",
            model=policy.strong_model,
            reason=f"Policy '{request.route_policy}' defaulted to strong model.",
        )

    return RoutingDecision(
        route="fast_model",
        model=policy.fast_model,
        reason=f"Policy '{request.route_policy}' defaulted to fast model.",
    )
