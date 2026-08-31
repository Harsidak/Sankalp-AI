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
    """OpenAI-compatible LLM provider (GPT-4o, GPT-4o-mini, etc.)."""

    provider_name = "openai"

    def __init__(self):
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            raise AIServiceError("OpenAI SDK not installed. Run: pip install openai")
        except Exception as e:
            raise AIServiceError(f"Failed to initialize OpenAI client: {e}")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs,
    ) -> dict:
        model = model or settings.default_llm_model
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            return {
                "content": response.choices[0].message.content,
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
        model = model or settings.default_llm_model
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise AIServiceError(f"OpenAI streaming error: {str(e)}")

    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        model = model or "text-embedding-3-small"

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
# Google Gemini Provider
# =============================================================================

class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider."""

    provider_name = "gemini"

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
        model_name = model or "gemini-1.5-flash"

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
        model_name = model or "gemini-1.5-flash"

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


def get_available_models() -> list[dict]:
    """Return metadata about all available AI models."""
    models = []

    if settings.openai_api_key:
        models.extend([
            {
                "name": "gpt-4o-mini",
                "provider": "openai",
                "description": "Fast, affordable model for most tasks",
                "max_tokens": 4096,
                "supports_streaming": True,
            },
            {
                "name": "gpt-4o",
                "provider": "openai",
                "description": "Most capable OpenAI model",
                "max_tokens": 4096,
                "supports_streaming": True,
            },
        ])

    if settings.google_api_key:
        models.extend([
            {
                "name": "gemini-1.5-flash",
                "provider": "gemini",
                "description": "Fast Gemini model for most tasks",
                "max_tokens": 8192,
                "supports_streaming": True,
            },
            {
                "name": "gemini-1.5-pro",
                "provider": "gemini",
                "description": "Most capable Gemini model",
                "max_tokens": 8192,
                "supports_streaming": True,
            },
        ])

    return models
