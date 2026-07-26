"""Adaptador de OpenAI que implementa :class:`LLMProvider`."""

from __future__ import annotations

from typing import Any

from app.ai.interfaces import LLMMessage, LLMResponse
from app.config import get_settings
from app.config.logging import get_logger
from app.core.errors import ExternalServiceError

logger = get_logger(__name__)


class OpenAIProvider:
    """Genera texto usando la API de OpenAI (Chat Completions)."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = "gpt-4o-mini",
        timeout: float = 60.0,
        default_max_tokens: int = 1200,
    ) -> None:
        if not api_key:
            raise ValueError("Se requiere OPENAI_API_KEY para OpenAIProvider.")
        # Import perezoso: la dependencia solo se necesita si se usa este proveedor.
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)
        self._model = model
        self._default_max_tokens = default_max_tokens

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Llama a OpenAI y devuelve la respuesta normalizada."""
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens or self._default_max_tokens,
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        try:
            response = await self._client.chat.completions.create(**payload)
        except Exception as exc:  # noqa: BLE001 - normalizamos cualquier fallo del SDK
            logger.exception("Fallo al llamar a OpenAI")
            raise ExternalServiceError(f"Error de OpenAI: {exc}") from exc

        choice = response.choices[0]
        usage = getattr(response, "usage", None)
        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            tokens_used=getattr(usage, "total_tokens", None),
        )


def build_openai_provider() -> OpenAIProvider:
    """Construye el proveedor OpenAI a partir de la configuración."""
    settings = get_settings()
    return OpenAIProvider(
        api_key=settings.openai_api_key,
        model=settings.openai_model,
        timeout=settings.openai_timeout_seconds,
        default_max_tokens=settings.openai_max_tokens,
    )
