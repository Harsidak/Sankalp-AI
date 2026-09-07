"""
Tests for the LLM provider layer.

These never touch a network: the point is the provider *selection* and
*model-resolution* logic, which is where a misconfiguration turns into a
confusing 404 from a vendor rather than a clear error from us.
"""

import pytest

from app.core.exceptions import AIServiceError
from app.services import ai_service
from app.services.ai_service import (
    GeminiProvider,
    NvidiaProvider,
    OpenAIProvider,
    get_available_models,
    get_provider,
)


@pytest.fixture(autouse=True)
def _clear_provider_cache():
    """`get_provider` memoises instances; tests must not inherit each other's."""
    ai_service._provider_instances.clear()
    yield
    ai_service._provider_instances.clear()


class _Settings:
    """Minimal stand-in for the settings singleton."""

    def __init__(self, **kw):
        self.openai_api_key = kw.get("openai_api_key")
        self.google_api_key = kw.get("google_api_key")
        self.nvidia_api_key = kw.get("nvidia_api_key")
        self.nvidia_base_url = kw.get(
            "nvidia_base_url", "https://integrate.api.nvidia.com/v1"
        )
        self.default_llm_provider = kw.get("default_llm_provider", "nvidia")
        self.default_llm_model = kw.get("default_llm_model", "some/model")


@pytest.fixture
def settings(monkeypatch):
    """Swap the module-level settings for a controllable one."""

    def _apply(**kw):
        s = _Settings(**kw)
        monkeypatch.setattr(ai_service, "settings", s)
        return s

    return _apply


# --- model resolution --------------------------------------------------------

def test_default_model_applies_only_to_the_default_provider(settings):
    """
    The regression this guards: DEFAULT_LLM_MODEL used to be applied by every
    provider, so switching provider mid-request sent an NVIDIA model name to
    Gemini (or vice versa) and produced a vendor 404 instead of a sane default.
    """
    settings(
        default_llm_provider="nvidia",
        default_llm_model="nvidia/nemotron-3.5-lightning-30b-a3b",
    )

    # Bypass __init__ — resolve_model needs no client.
    nvidia = NvidiaProvider.__new__(NvidiaProvider)
    gemini = GeminiProvider.__new__(GeminiProvider)
    openai = OpenAIProvider.__new__(OpenAIProvider)

    assert nvidia.resolve_model(None) == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert gemini.resolve_model(None) == GeminiProvider.fallback_model
    assert openai.resolve_model(None) == OpenAIProvider.fallback_model

    # An explicit request beats both.
    assert gemini.resolve_model("gemini-1.5-pro") == "gemini-1.5-pro"
    assert nvidia.resolve_model("openai/gpt-oss-20b") == "openai/gpt-oss-20b"


# --- provider factory --------------------------------------------------------

def test_unknown_provider_is_rejected(settings):
    settings(nvidia_api_key="nvapi-test")
    with pytest.raises(AIServiceError, match="Unknown LLM provider"):
        get_provider("not-a-provider")


def test_missing_key_fails_with_our_error_not_the_vendors(settings):
    """An unconfigured provider should fail at construction, not at call time."""
    settings(nvidia_api_key=None)
    with pytest.raises(AIServiceError, match="No API key configured"):
        get_provider("nvidia")


def test_nvidia_provider_is_configured_from_settings(settings):
    settings(nvidia_api_key="nvapi-test", nvidia_base_url="https://example.test/v1")
    provider = get_provider("nvidia")

    assert isinstance(provider, NvidiaProvider)
    assert provider.provider_name == "nvidia"
    # Reasoning traces must stay off: they consume the token budget and would
    # otherwise be streamed into a wellness reply.
    assert provider.extra_body == {"chat_template_kwargs": {"thinking": False}}
    assert str(provider.client.base_url).startswith("https://example.test")


def test_provider_instances_are_cached(settings):
    settings(nvidia_api_key="nvapi-test")
    assert get_provider("nvidia") is get_provider("nvidia")


# --- model catalogue ---------------------------------------------------------

def test_catalogue_hides_models_whose_key_is_unset(settings):
    settings(nvidia_api_key="nvapi-test", openai_api_key=None, google_api_key=None)
    providers = {m["provider"] for m in get_available_models()}
    assert providers == {"nvidia"}


def test_catalogue_marks_exactly_one_default(settings):
    settings(
        nvidia_api_key="nvapi-test",
        default_llm_provider="nvidia",
        default_llm_model="nvidia/nemotron-3.5-lightning-30b-a3b",
    )
    models = get_available_models()
    defaults = [m for m in models if m["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["name"] == "nvidia/nemotron-3.5-lightning-30b-a3b"


def test_catalogue_is_empty_when_nothing_is_configured(settings):
    settings(nvidia_api_key=None, openai_api_key=None, google_api_key=None)
    assert get_available_models() == []
