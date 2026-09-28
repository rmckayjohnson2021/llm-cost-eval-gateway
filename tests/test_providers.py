from gateway.providers import (
    MockProvider,
    OpenAIProvider,
    create_provider_from_env,
    resolve_openai_model,
)


def test_provider_factory_defaults_to_mock(monkeypatch):
    monkeypatch.delenv("GATEWAY_PROVIDER", raising=False)

    provider = create_provider_from_env()

    assert isinstance(provider, MockProvider)


def test_provider_factory_selects_openai(monkeypatch):
    monkeypatch.setenv("GATEWAY_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    provider = create_provider_from_env()

    assert isinstance(provider, OpenAIProvider)


def test_openai_provider_returns_error_without_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "replace_me")

    result = OpenAIProvider().complete("hello", "openai-fast", 10)

    assert result.error_type == "missing_api_key"


def test_openai_provider_rejects_mock_policy_models():
    result = OpenAIProvider(api_key="test-key").complete("hello", "mock-fast", 10)

    assert result.error_type == "provider_policy_mismatch"


def test_openai_alias_requires_model_env_value(monkeypatch):
    monkeypatch.setenv("DEFAULT_FAST_MODEL", "replace_me")

    assert resolve_openai_model("openai-fast") is None


def test_openai_alias_resolves_from_environment(monkeypatch):
    monkeypatch.setenv("DEFAULT_FAST_MODEL", "gpt-5-mini")

    assert resolve_openai_model("openai-fast") == "gpt-5-mini"
