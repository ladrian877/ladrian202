"""Jerarquía de errores de dominio.

Los servicios lanzan estas excepciones y la capa API las traduce a respuestas
HTTP. Así la lógica de negocio no depende de FastAPI ni de códigos HTTP.
"""

from __future__ import annotations


class DomainError(Exception):
    """Error base del dominio. Lleva un mensaje y un código HTTP sugerido."""

    status_code: int = 400

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class NotFoundError(DomainError):
    """La entidad solicitada no existe."""

    status_code = 404


class ValidationError(DomainError):
    """Los datos de entrada no son válidos para la operación."""

    status_code = 422


class ExternalServiceError(DomainError):
    """Un servicio externo (Places, OpenAI, web) falló de forma irrecuperable."""

    status_code = 502
