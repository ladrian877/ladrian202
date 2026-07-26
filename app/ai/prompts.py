"""Plantillas de prompts para informe y email.

Las funciones construyen los mensajes de chat que se envían al LLM. Incluyen las
conclusiones estructuradas (derivadas del análisis real) para que el modelo
redacte una prosa fiel a los datos, evitando inventar problemas inexistentes.
"""

from __future__ import annotations

import json

from app.ai.insights import ReportFindings
from app.ai.interfaces import LLMMessage
from app.models.company import Company

_REPORT_SYSTEM = (
    "Eres un consultor senior de marketing digital. Redactas informes claros, "
    "honestos y accionables para una agencia. No inventes datos: básate solo en "
    "la información proporcionada. Responde en español."
)

_EMAIL_SYSTEM = (
    "Eres un copywriter experto en captación B2B. Escribes emails de prospección "
    "cercanos, personalizados y NADA spam. Mencionas problemas reales detectados y "
    "ofreces soluciones concretas sin exagerar. Tono profesional y humano, en español. "
    "El email debe ser breve (120-180 palabras)."
)


def report_summary_messages(company: Company, findings: ReportFindings) -> list[LLMMessage]:
    """Mensajes para pedir al LLM un resumen ejecutivo del informe."""
    context = {
        "empresa": company.name,
        "categoria": company.category,
        "ciudad": company.city,
        "fortalezas": findings.strengths,
        "debilidades": findings.weaknesses,
        "oportunidades": findings.opportunities,
        "prioridad": findings.priority,
    }
    user = (
        "Redacta un resumen ejecutivo (máx. 120 palabras) del estado digital de la "
        "empresa a partir de estos datos. No uses viñetas, solo un párrafo fluido.\n\n"
        f"Datos:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    )
    return [
        LLMMessage(role="system", content=_REPORT_SYSTEM),
        LLMMessage(role="user", content=user),
    ]


def email_messages(company: Company, findings: ReportFindings) -> list[LLMMessage]:
    """Mensajes para pedir al LLM el email de contacto personalizado."""
    context = {
        "empresa": company.name,
        "categoria": company.category,
        "ciudad": company.city,
        "problemas_detectados": findings.weaknesses[:3],
        "servicios_ofrecidos": findings.suggested_services[:3],
    }
    user = (
        "Escribe un email de prospección para esta empresa. Debe:\n"
        "- Saludar de forma cercana.\n"
        "- Mencionar 2-3 problemas reales de la lista.\n"
        "- Ofrecer los servicios correspondientes como solución.\n"
        "- Terminar proponiendo una llamada breve sin compromiso.\n"
        "Devuelve SOLO el cuerpo del email (sin asunto).\n\n"
        f"Datos:\n{json.dumps(context, ensure_ascii=False, indent=2)}"
    )
    return [
        LLMMessage(role="system", content=_EMAIL_SYSTEM),
        LLMMessage(role="user", content=user),
    ]


def email_subject(company: Company) -> str:
    """Asunto por defecto del email (corto y sin clickbait)."""
    return f"Ideas para conseguir más clientes en {company.name}"
