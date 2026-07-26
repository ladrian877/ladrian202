"""Analizador de vías de contacto (formulario, email, teléfono)."""

from __future__ import annotations

import re
from typing import Any

from app.analyzers.interfaces import AnalysisContext

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_FORM_FIELD_HINTS = ("email", "correo", "mensaje", "message", "nombre", "name", "asunto")


class ContactAnalyzer:
    """Detecta si la web ofrece un formulario u otras vías de contacto."""

    name = "contact"

    async def analyze(self, context: AnalysisContext) -> dict[str, Any]:
        soup = context.soup
        forms = soup.find_all("form")
        contact_form = any(self._looks_like_contact_form(form) for form in forms)

        has_mailto = bool(
            soup.find("a", href=lambda v: bool(v) and v.lower().startswith("mailto:"))
        )
        has_tel = bool(soup.find("a", href=lambda v: bool(v) and v.lower().startswith("tel:")))
        has_email_text = bool(_EMAIL_RE.search(context.html))

        return {
            "contact_form": contact_form,
            "contact_findings": {
                "forms_count": len(forms),
                "mailto": has_mailto,
                "tel_link": has_tel,
                "email_in_text": has_email_text,
            },
        }

    @staticmethod
    def _looks_like_contact_form(form: Any) -> bool:
        text = str(form).lower()
        has_input = bool(form.find_all(("input", "textarea")))
        mentions_contact = any(hint in text for hint in _FORM_FIELD_HINTS)
        return has_input and mentions_contact
