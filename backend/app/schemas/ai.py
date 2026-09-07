"""
AI inference request/response schemas.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    """One prior turn of a conversation, replayed to give the model context."""
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=10000)


class InferenceRequest(BaseModel):
    """Request for AI text generation."""
    prompt: str = Field(..., min_length=1, max_length=10000)
    # Prior turns, oldest first. The API is stateless, so the client replays
    # context on each call; capped so a long chat cannot blow the context
    # window or the token budget.
    history: list[ChatTurn] = Field(default_factory=list, max_length=20)
    system_prompt: Optional[str] = Field(None, max_length=5000)
    model: Optional[str] = None  # Override default model
    provider: Optional[str] = None  # Override default provider ("nvidia", "openai", "gemini")
    max_tokens: int = Field(1024, ge=1, le=8192)
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    stream: bool = False


class InferenceResponse(BaseModel):
    """Response from AI text generation."""
    content: str
    model: str
    provider: str
    usage: Optional[dict] = None  # Token usage stats


class StreamChunk(BaseModel):
    """A single chunk in a streaming AI response."""
    content: str
    done: bool = False
    model: Optional[str] = None


class ReflectionRequest(BaseModel):
    """Ask the companion to reflect on something the user wrote."""
    text: str = Field(..., min_length=1, max_length=8000)
    tone: str = Field(
        "supportive",
        description="One of: supportive, practical, curious",
    )


class ReflectionResponse(BaseModel):
    """A short reflection generated from the user's text."""
    reflection: str
    model: str
    provider: str


class ModelInfo(BaseModel):
    """Information about an available AI model."""
    name: str
    provider: str
    description: Optional[str] = None
    max_tokens: int
    supports_streaming: bool = True
    is_default: bool = False
