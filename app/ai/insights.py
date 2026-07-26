"""Generación determinista de conclusiones a partir del análisis y el score.

Estas funciones producen contenido *real* (derivado de los datos) que sirve
tanto de fuente de verdad estructurada del informe como de borrador de respaldo
cuando el proveedor de IA no genera texto (modo sin API). Cuando hay IA, el
modelo redacta la prosa a partir de esta misma información.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from app.models.company import Company
from app.models.website_analysis import WebsiteAnalysis

# Descripción de cada problema y el servicio de agencia que lo resuelve.
_PROBLEM_TEXT: dict[str, tuple[str, str]] = {
    "no_website": (
        "La empresa no dispone de sitio web.",
        "Diseño y desarrollo de una web profesional.",
    ),
    "no_https": (
        "La web no usa HTTPS, lo que afecta a la seguridad y al SEO.",
        "Instalación de certificado SSL y migración a HTTPS.",
    ),
    "not_responsive": (
        "El diseño no es responsive: mala experiencia en móvil.",
        "Rediseño responsive optimizado para dispositivos móviles.",
    ),
    "poor_performance": (
        "El rendimiento y la velocidad de carga son mejorables.",
        "Optimización de velocidad y Core Web Vitals.",
    ),
    "poor_seo": (
        "El SEO on-page presenta carencias (títulos, descripciones, encabezados).",
        "Auditoría y optimización SEO on-page.",
    ),
    "no_social_media": (
        "No hay presencia detectable en redes sociales.",
        "Gestión de redes sociales y creación de perfiles.",
    ),
    "no_contact_form": (
        "No se detecta un formulario de contacto que capte leads.",
        "Implementación de formularios y captación de leads.",
    ),
    "no_analytics": (
        "No hay analítica web instalada (Analytics/Tag Manager).",
        "Configuración de analítica y medición de conversiones.",
    ),
    "no_blog": (
        "No existe blog ni sección de contenidos para atraer tráfico.",
        "Marketing de contenidos y estrategia de blog.",
    ),
    "unoptimized_images": (
        "Hay imágenes sin optimizar que ralentizan la web.",
        "Optimización de imágenes y recursos.",
    ),
    "broken_links": (
        "Se han detectado enlaces rotos que dañan la experiencia y el SEO.",
        "Corrección de enlaces rotos y auditoría técnica.",
    ),
}

# Fortalezas detectables (condición sobre el análisis -> texto).
_STRENGTH_CHECKS: list[tuple[str, str]] = [
    ("https", "La web utiliza HTTPS."),
    ("responsive", "El diseño es responsive y se adapta a móvil."),
    ("google_analytics", "Tiene analítica web instalada."),
    ("contact_form", "Dispone de formulario de contacto."),
    ("has_blog", "Cuenta con un blog o sección de contenidos."),
]


@dataclass(slots=True)
class ReportFindings:
    """Conclusiones estructuradas del informe (fuente de verdad)."""

    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)
    opportunities: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    suggested_services: list[str] = field(default_factory=list)
    priority: str = "low"

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


def build_report_findings(
    company: Company,
    analysis: WebsiteAnalysis | None,
    score_breakdown: dict[str, object] | None,
    priority: str,
) -> ReportFindings:
    """Construye las conclusiones estructuradas a partir de los datos."""
    problems: list[str] = []
    if score_breakdown and isinstance(score_breakdown.get("problems"), list):
        problems = [str(p) for p in score_breakdown["problems"]]  # type: ignore[index]

    findings = ReportFindings(priority=priority)

    for key in problems:
        text = _PROBLEM_TEXT.get(key)
        if text:
            findings.weaknesses.append(text[0])
            findings.suggested_services.append(text[1])
            findings.opportunities.append(
                f"Oportunidad de mejora: {text[0].rstrip('.').lower()}."
            )

    # Fortalezas a partir del análisis (si lo hay).
    if analysis is not None and analysis.status == "completed":
        for attr, msg in _STRENGTH_CHECKS:
            if getattr(analysis, attr, None) is True:
                findings.strengths.append(msg)
    if company.rating and company.rating >= 4:
        findings.strengths.append(
            f"Buena reputación online ({company.rating}★, {company.reviews_count or 0} reseñas)."
        )

    # Recomendaciones = primeros servicios sugeridos, sin duplicar.
    seen: set[str] = set()
    for service in findings.suggested_services:
        if service not in seen:
            seen.add(service)
            findings.recommendations.append(service)

    if not findings.weaknesses:
        findings.weaknesses.append("No se han detectado carencias digitales relevantes.")
    return findings


def build_report_summary(company: Company, findings: ReportFindings) -> str:
    """Resumen en prosa (borrador de respaldo si no hay IA)."""
    weakness_count = len(findings.weaknesses)
    top = "; ".join(findings.weaknesses[:3])
    return (
        f"{company.name} presenta {weakness_count} área(s) de mejora en su presencia "
        f"digital. Puntos principales: {top}. Prioridad del lead: {findings.priority}."
    )


def build_email_draft(company: Company, findings: ReportFindings) -> tuple[str, str]:
    """Asunto y cuerpo del email (borrador de respaldo si no hay IA)."""
    problems = findings.weaknesses[:3]
    problems_text = "\n".join(f"  • {p}" for p in problems)
    services = findings.suggested_services[:3]
    services_text = "\n".join(f"  • {s}" for s in services)

    subject = f"Ideas para mejorar la presencia online de {company.name}"
    body = (
        f"Hola, equipo de {company.name}:\n\n"
        "Hemos echado un vistazo a vuestra presencia digital y hemos visto "
        "algunas oportunidades concretas para conseguir más clientes:\n\n"
        f"{problems_text}\n\n"
        "Son mejoras muy asumibles que podrían tener un impacto directo en "
        "vuestras reservas/ventas. Desde nuestra agencia podríamos ayudaros con:\n\n"
        f"{services_text}\n\n"
        "Si os encaja, encantados de enseñaros un par de ejemplos en una llamada "
        "breve de 15 minutos, sin compromiso.\n\n"
        "Un saludo."
    )
    return subject, body
