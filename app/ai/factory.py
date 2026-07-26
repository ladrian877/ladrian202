"""Factoría del proveedor de IA según la configuración."""

from __future__ import annotations

from app.ai.interfaces import LLMProvider
from app.ai.null_provider import NullLLMProvider
from app.config import get_settings
from app.config.settings import LLMProviderName


def build_llm_provider() -> LLMProvider:
    """Devuelve el proveedor de IA efectivo.

    Usa OpenAI si hay clave configurada; en caso contrario, el proveedor nulo
    determinista (para desarrollo y tests sin API).
    """
    settings = get_settings()
    if settings.effective_llm_provider == LLMProviderName.OPENAI:
        from app.ai.openai_provider import build_openai_provider

        return build_openai_provider()
    return NullLLMProvider()
