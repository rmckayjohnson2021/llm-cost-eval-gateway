import pytest

from gateway.policies import get_policy, load_policy_catalog
from gateway.routing import choose_route
from gateway.schemas import ModelRequest


def make_request(input_text: str, route_policy: str) -> ModelRequest:
    return ModelRequest(
        app_name="test",
        workflow_version="v1",
        simulated_user_id="user-1",
        simulated_team_id="team-1",
        input_text=input_text,
        route_policy=route_policy,
    )


def test_policy_catalog_loads_expected_policies():
    catalog = load_policy_catalog()

    assert {"fast_only", "strong_only", "routed"} <= set(catalog.policies)


def test_fast_only_policy_routes_to_fast_model():
    decision = choose_route(make_request("sev1 outage with executive impact", "fast_only"))

    assert decision.route == "fast_model"
    assert decision.model == "mock-fast"


def test_strong_only_policy_routes_to_strong_model():
    decision = choose_route(make_request("routine import issue", "strong_only"))

    assert decision.route == "strong_model"
    assert decision.model == "mock-strong"


def test_routed_policy_sends_ambiguous_work_to_human_review():
    decision = choose_route(make_request("unclear conflicting dashboard signals", "routed"))

    assert decision.route == "human_review"
    assert decision.model is None


def test_routed_policy_sends_high_impact_work_to_strong_model():
    decision = choose_route(make_request("sev1 outage for executive report", "routed"))

    assert decision.route == "strong_model"
    assert decision.model == "mock-strong"


def test_routed_policy_uses_metadata_routing_text_before_prompt_text():
    request = make_request(
        "Prompt instructions mention unclear ambiguous evidence, but that is not the incident.",
        "routed",
    )
    request.metadata["routing_text"] = "schema validation failed after vendor added loyalty_tier column"

    decision = choose_route(request)

    assert decision.route == "strong_model"
    assert decision.model == "mock-strong"


def test_unknown_policy_fails_with_available_names():
    with pytest.raises(ValueError, match="fast_only"):
        get_policy("missing_policy")
