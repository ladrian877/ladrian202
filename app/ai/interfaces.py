"""Contrato del proveedor de IA (LLM).

Abstraer el proveedor permite cambiar OpenAI por Claude u otro sin tocar la
lógica de negocio (informes, emails). El método principal, :meth:`complete`,
recibe mensajes de chat y opciones, y devuelve texto + metadatos de uso.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(slots=True)
class LLMMessage:
    """Un mensaje de la conversación con roles ``system``/``user``/``assistant``."""

    role: str
    content: str


@dataclass(slots=True)
class LLMResponse:
    """Respuesta del proveedor: texto generado y metadatos."""

    content: str
    model: str
    tokens_used: int | None = None
    raw: dict[str, object] = field(default_factory=dict)


@runtime_checkable
class LLMProvider(Protocol):
    """Proveedor de generación de texto por chat."""

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Genera una respuesta a partir de la conversación dada."""
        ...
