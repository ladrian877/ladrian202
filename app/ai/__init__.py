"""Capa de IA: proveedor LLM abstracto, prompts y utilidades."""

from app.ai.factory import build_llm_provider
from app.ai.interfaces import LLMMessage, LLMProvider, LLMResponse

__all__ = ["LLMProvider", "LLMMessage", "LLMResponse", "build_llm_provider"]
