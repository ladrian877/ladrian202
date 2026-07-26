"""Proveedor de IA determinista para desarrollo y tests (sin API).

Devuelve contenido vacío de forma intencionada: los servicios que lo consumen
(informe, email) construyen un borrador determinista a partir del análisis real
y lo usan como *fallback* cuando el proveedor no genera texto. Así el flujo
completo funciona sin clave de API y con salidas reproducibles.
"""

from __future__ import annotations

from app.ai.interfaces import LLMMessage, LLMResponse


class NullLLMProvider:
    """Proveedor que no llama a ninguna API; señaliza 'sin generación'."""

    async def complete(
        self,
        messages: list[LLMMessage],
        *,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        json_mode: bool = False,
    ) -> LLMResponse:
        """Devuelve una respuesta vacía; el servicio usará su borrador."""
        return LLMResponse(content="", model="null", tokens_used=0)
