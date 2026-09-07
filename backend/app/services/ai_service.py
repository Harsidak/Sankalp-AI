"""
AI service: LLM provider abstraction for inference and embeddings.

Implements the Strategy pattern with a base class and pluggable providers.
Adding a new provider (Anthropic, Mistral, Ollama) requires only a new subclass.
"""

import logging
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional

from app.config import get_settings
from app.core.exceptions import AIServiceError

settings = get_settings()
logger = logging.getLogger("sankalp.ai")


# =============================================================================
# Base Provider (Abstract)
# =============================================================================

class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    All providers must implement generate(), stream(), and embed().
    """

    provider_name: str = "base"
    fallback_model: str = ""

    @staticmethod
    def build_messages(
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[list[dict]] = None,
    ) -> list[dict]:
        """
        Assemble the chat-completions message list.

        `history` is prior turns, oldest first, and goes between the system
        prompt and the new turn -- the order is the context the model reads,
        so appending history after the prompt would make it answer the wrong
        message.
        """
        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        for turn in history or []:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": prompt})
        return messages

    def resolve_model(self, requested: Optional[str]) -> str:
        """
        Pick the model name to send for this provider.

        An explicit request always wins. Otherwise `DEFAULT_LLM_MODEL` applies
        only to the provider it was configured alongside -- a model name is
        provider-specific, so handing "nvidia/nemotron-..." to Gemini (or
        "gpt-4o-mini" to NVIDIA) would be a guaranteed 404. Every other
        provider falls back to its own known-good default.
        """
        if requested:
            return requested
        if (
            settings.default_llm_provider == self.provider_name
            and settings.default_llm_model
        ):
            return settings.default_llm_model
        return self.fallback_model

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs,
    ) -> dict:
        """
        Generate a complete text response.

        Returns:
            Dict with keys: content, model, provider, usage
        """
        ...

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Stream text tokens as they're generated.

        Yields:
            Individual text chunks/tokens.
        """
        ...

    @abstractmethod
    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """
        Generate embedding vectors for a list of texts.

        Returns:
            List of embedding vectors (list of floats).
        """
        ...


# =============================================================================
# OpenAI Provider
# =============================================================================

class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI-compatible LLM provider (GPT-4o, GPT-4o-mini, etc.).

    The API key and base URL are constructor arguments rather than reads of
    `settings`, which is what lets any OpenAI-wire-format gateway reuse this
    class -- see `NvidiaProvider` below.
    """

    provider_name = "openai"
    fallback_model = "gpt-4o-mini"
    embedding_model = "text-embedding-3-small"

    # Vendor-specific request fields, merged into every call. Empty here;
    # subclasses override it (NVIDIA uses it to switch off reasoning traces).
    extra_body: dict = {}

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        api_key = api_key or settings.openai_api_key
        if not api_key:
            raise AIServiceError(
                f"No API key configured for provider '{self.provider_name}'."
            )
        try:
            from openai import AsyncOpenAI
            # A read timeout is essential here: reasoning models on shared
            # inference endpoints can stall for minutes, and without a bound
            # the request holds a worker until the client gives up.
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=60.0,
                max_retries=1,
            )
        except ImportError:
            raise AIServiceError("OpenAI SDK not installed. Run: pip install openai")
        except Exception as e:
            raise AIServiceError(f"Failed to initialize {self.provider_name} client: {e}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs,
    ) -> dict:
        model = self.resolve_model(model)
        messages = self.build_messages(prompt, system_prompt, kwargs.get("history"))

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **({"extra_body": self.extra_body} if self.extra_body else {}),
            )

            # Reasoning models put their scratchpad in `reasoning_content` and
            # the answer in `content`. We only ever surface `content`; if the
            # model spent its whole budget thinking, that field comes back
            # empty and an empty string is a friendlier failure than None.
            return {
                "content": response.choices[0].message.content or "",
                "model": response.model,
                "provider": self.provider_name,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                } if response.usage else None,
            }
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise AIServiceError(f"OpenAI API error: {str(e)}")

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        model = self.resolve_model(model)
        messages = self.build_messages(prompt, system_prompt, kwargs.get("history"))

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
                **({"extra_body": self.extra_body} if self.extra_body else {}),
            )

            async for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                # `delta.reasoning_content` (NVIDIA/DeepSeek reasoning models)
                # is deliberately dropped -- it is the model's scratchpad, not
                # an answer, and streaming it would leak chain-of-thought into
                # the chat bubble.
                if delta.content:
                    yield delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise AIServiceError(f"OpenAI streaming error: {str(e)}")

    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        model = model or self.embedding_model

        try:
            response = await self.client.embeddings.create(
                model=model,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise AIServiceError(f"OpenAI embedding error: {str(e)}")


# =============================================================================
# NVIDIA NIM Provider
# =============================================================================

class NvidiaProvider(OpenAIProvider):
    """
    NVIDIA NIM (build.nvidia.com) provider.

    NIM exposes the OpenAI chat-completions wire format, so the whole
    integration is a base URL, a key, and two vendor quirks -- which is the
    point of keeping `OpenAIProvider` parameterised. No new SDK, no new
    request/response mapping.
    """

    provider_name = "nvidia"
    fallback_model = "nvidia/nemotron-3.5-lightning-30b-a3b"
    embedding_model = "nvidia/nv-embedqa-mistral-7b-v2"

    # Quirk 1: most NIM reasoning models expose a chat-template switch. Left
    # on, they burn the token budget on a scratchpad and a short reflection
    # comes back empty. We do not want reasoning traces in a wellness reply,
    # so it is off. Non-reasoning models ignore the flag.
    extra_body = {"chat_template_kwargs": {"thinking": False}}

    def __init__(self):
        super().__init__(
            api_key=settings.nvidia_api_key,
            base_url=settings.nvidia_base_url,
        )

    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """
        Quirk 2: NVIDIA's retrieval embedding models are asymmetric -- they
        require an `input_type` telling them whether the text is a query or a
        stored passage. OpenAI's API has no such field, so this cannot share
        the parent implementation.
        """
        model = model or self.embedding_model
        try:
            response = await self.client.embeddings.create(
                model=model,
                input=texts,
                extra_body={"input_type": "passage", "truncate": "END"},
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"NVIDIA embedding error: {e}")
            raise AIServiceError(f"NVIDIA embedding error: {str(e)}")


# =============================================================================
# Google Gemini Provider
# =============================================================================

class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider."""

    provider_name = "gemini"
    fallback_model = "gemini-1.5-flash"

    def __init__(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.google_api_key)
            self.genai = genai
        except ImportError:
            raise AIServiceError(
                "Google Generative AI SDK not installed. "
                "Run: pip install google-generativeai"
            )
        except Exception as e:
            raise AIServiceError(f"Failed to initialize Gemini client: {e}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs,
    ) -> dict:
        model_name = self.resolve_model(model)

        try:
            gen_model = self.genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
            )

            generation_config = self.genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            response = await gen_model.generate_content_async(
                prompt,
                generation_config=generation_config,
            )

            return {
                "content": response.text,
                "model": model_name,
                "provider": self.provider_name,
                "usage": None,  # Gemini doesn't always expose token counts
            }
        except Exception as e:
            logger.error(f"Gemini generation error: {e}")
            raise AIServiceError(f"Gemini API error: {str(e)}")

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        model_name = self.resolve_model(model)

        try:
            gen_model = self.genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
            )

            generation_config = self.genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )

            response = await gen_model.generate_content_async(
                prompt,
                generation_config=generation_config,
                stream=True,
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            raise AIServiceError(f"Gemini streaming error: {str(e)}")

    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        model_name = model or "models/text-embedding-004"

        try:
            embeddings = []
            for text in texts:
                result = self.genai.embed_content(
                    model=model_name,
                    content=text,
                )
                embeddings.append(result["embedding"])
            return embeddings
        except Exception as e:
            logger.error(f"Gemini embedding error: {e}")
            raise AIServiceError(f"Gemini embedding error: {str(e)}")


# =============================================================================
# Provider Factory
# =============================================================================

# Registry of available providers
_PROVIDERS: dict[str, type[BaseLLMProvider]] = {
    "openai": OpenAIProvider,
    "nvidia": NvidiaProvider,
    "gemini": GeminiProvider,
}

# Cached provider instances
_provider_instances: dict[str, BaseLLMProvider] = {}


def get_provider(name: Optional[str] = None) -> BaseLLMProvider:
    """
    Get an LLM provider instance by name.

    Uses a cached singleton per provider name.
    Falls back to the default provider from settings.

    Args:
        name: Provider name ("openai" or "gemini"). Defaults to settings.

    Returns:
        Configured LLM provider instance.

    Raises:
        AIServiceError: If provider name is unknown or initialization fails.
    """
    provider_name = name or settings.default_llm_provider

    if provider_name not in _PROVIDERS:
        raise AIServiceError(
            f"Unknown LLM provider: '{provider_name}'. "
            f"Available: {list(_PROVIDERS.keys())}"
        )

    if provider_name not in _provider_instances:
        _provider_instances[provider_name] = _PROVIDERS[provider_name]()

    return _provider_instances[provider_name]


# Static catalogue of models we have actually exercised, grouped by the
# setting that unlocks them. NVIDIA publishes ~80 models at /v1/models, but
# listing all of them would offer the user models this app has never called;
# these are the ones with measured latency and known behaviour.
_MODEL_CATALOGUE: list[tuple[str, dict]] = [
    ("openai_api_key", {
        "name": "gpt-4o-mini", "provider": "openai",
        "description": "Fast, affordable model for most tasks",
        "max_tokens": 4096, "supports_streaming": True,
    }),
    ("openai_api_key", {
        "name": "gpt-4o", "provider": "openai",
        "description": "Most capable OpenAI model",
        "max_tokens": 4096, "supports_streaming": True,
    }),
    ("nvidia_api_key", {
        "name": "nvidia/nemotron-3.5-lightning-30b-a3b", "provider": "nvidia",
        "description": "Default. Fast, no reasoning trace (~2s to first token)",
        "max_tokens": 4096, "supports_streaming": True,
    }),
    ("nvidia_api_key", {
        "name": "openai/gpt-oss-20b", "provider": "nvidia",
        "description": "Open-weight, lowest latency of the tested set",
        "max_tokens": 4096, "supports_streaming": True,
    }),
    ("nvidia_api_key", {
        "name": "deepseek-ai/deepseek-v4-flash-0731", "provider": "nvidia",
        "description": "DeepSeek V4 Flash — stronger, noticeably slower",
        "max_tokens": 8192, "supports_streaming": True,
    }),
    ("nvidia_api_key", {
        "name": "deepseek-ai/deepseek-v4-pro-0813", "provider": "nvidia",
        "description": "DeepSeek V4 Pro — highest quality, slowest; not for live demo",
        "max_tokens": 8192, "supports_streaming": True,
    }),
    ("google_api_key", {
        "name": "gemini-1.5-flash", "provider": "gemini",
        "description": "Fast Gemini model for most tasks",
        "max_tokens": 8192, "supports_streaming": True,
    }),
    ("google_api_key", {
        "name": "gemini-1.5-pro", "provider": "gemini",
        "description": "Most capable Gemini model",
        "max_tokens": 8192, "supports_streaming": True,
    }),
]


def get_available_models() -> list[dict]:
    """
    Return metadata for every model whose provider is actually configured.

    Driven off the settings object, so an unset key silently removes its
    models from the list instead of offering the user a call that will 401.
    """
    return [
        dict(model, is_default=(
            model["provider"] == settings.default_llm_provider
            and model["name"] == settings.default_llm_model
        ))
        for key, model in _MODEL_CATALOGUE
        if getattr(settings, key, None)
    ]
