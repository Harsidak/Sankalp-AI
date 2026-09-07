"""
AI router.

The AI surface is deliberately thin: one reflection endpoint the product
actually uses, plus the raw inference endpoints behind it. There is no
prompt chain, memory store, or analysis pipeline -- a reflection is a
single call to the configured provider.
"""

import json

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.ai import (
    InferenceRequest,
    InferenceResponse,
    ModelInfo,
    ReflectionRequest,
    ReflectionResponse,
)
from app.schemas.common import APIResponse
from app.services.ai_service import get_available_models, get_provider

router = APIRouter(prefix="/ai", tags=["AI"])


# The companion's persona. It lives here, not in the browser, for two reasons:
# a client-supplied persona can be rewritten in devtools, and the safety lines
# (no diagnosis, no medication, escalate on crisis) are the part of this app
# that must not be user-editable.
_COMPANION_SYSTEM_PROMPT = (
    "You are SanKalp, a wellness companion inside a mood-and-habit journalling "
    "app. Be warm, concrete and brief -- usually under 120 words. Reflect what "
    "the person is feeling before offering anything. Suggest at most one small "
    "next step, and only when it is wanted.\n"
    "You are not a clinician: never diagnose, never discuss medication, and "
    "never present yourself as therapy. If someone describes self-harm, abuse, "
    "or a crisis, say plainly that this is beyond what you can help with and "
    "encourage them to contact a local crisis line or someone they trust."
)


def _history_of(request: InferenceRequest) -> list[dict]:
    """Prior turns as plain dicts, which is what the provider layer expects."""
    return [turn.model_dump() for turn in request.history]


@router.post(
    "/inference",
    response_model=APIResponse[InferenceResponse],
    summary="Generate text (single-shot)",
)
async def inference(
    request: InferenceRequest,
    user: User = Depends(get_current_active_user),
):
    """
    Generate a complete text response from the LLM.
    For streaming responses, use /ai/stream instead.
    """
    provider = get_provider(request.provider)
    result = await provider.generate(
        prompt=request.prompt,
        system_prompt=request.system_prompt or _COMPANION_SYSTEM_PROMPT,
        model=request.model,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        history=_history_of(request),
    )
    return APIResponse(
        success=True,
        data=InferenceResponse(**result),
    )


@router.post(
    "/stream",
    summary="Generate text (streaming via SSE)",
)
async def stream_inference(
    request: InferenceRequest,
    user: User = Depends(get_current_active_user),
):
    """
    Stream generated text tokens via Server-Sent Events (SSE).
    Each event contains a JSON chunk with 'content' and 'done' fields.
    """
    provider = get_provider(request.provider)

    async def event_generator():
        try:
            async for token in provider.stream(
                prompt=request.prompt,
                system_prompt=request.system_prompt or _COMPANION_SYSTEM_PROMPT,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                history=_history_of(request),
            ):
                yield {
                    "event": "token",
                    "data": json.dumps({"content": token, "done": False}),
                }
            # Send completion signal
            yield {
                "event": "token",
                "data": json.dumps({"content": "", "done": True}),
            }
        except Exception as e:
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)}),
            }

    return EventSourceResponse(event_generator())


# Tone -> system prompt. Kept here rather than in the database because
# these are product copy, not user data.
_TONES = {
    "supportive": (
        "You are a warm, grounded wellness companion. Reflect back what the "
        "person seems to be feeling in two or three sentences. Do not give "
        "medical advice, do not diagnose, and do not be saccharine."
    ),
    "practical": (
        "You are a calm, practical wellness companion. In two or three "
        "sentences, name what the person is dealing with and suggest one "
        "small, concrete next step. Do not give medical advice."
    ),
    "curious": (
        "You are a thoughtful wellness companion. In two or three sentences, "
        "reflect what you notice and ask one open question that helps the "
        "person think further. Do not give medical advice."
    ),
}


@router.post(
    "/reflect",
    response_model=APIResponse[ReflectionResponse],
    summary="Reflect on a journal entry or check-in note",
)
async def reflect(
    request: ReflectionRequest,
    user: User = Depends(get_current_active_user),
):
    """
    Generate a short reflection on something the user wrote.

    One provider call, no stored state. If the tone is unrecognised it
    falls back to the supportive prompt rather than erroring, since a bad
    tone string should not cost the user their reflection.
    """
    system_prompt = _TONES.get(request.tone, _TONES["supportive"])

    provider = get_provider()
    result = await provider.generate(
        prompt=request.text,
        system_prompt=system_prompt,
        max_tokens=300,
        temperature=0.8,
    )

    return APIResponse(
        success=True,
        data=ReflectionResponse(
            reflection=result["content"],
            model=result.get("model", "unknown"),
            provider=result.get("provider", "unknown"),
        ),
    )


@router.get(
    "/models",
    response_model=APIResponse[list[ModelInfo]],
    summary="List available models",
)
async def list_models(
    user: User = Depends(get_current_active_user),
):
    """List all configured and available AI models."""
    models = get_available_models()
    return APIResponse(
        success=True,
        data=[ModelInfo(**m) for m in models],
    )
