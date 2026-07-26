"""Utilidades de dominio transversales (errores, tipos base)."""

from app.core.errors import (
    DomainError,
    ExternalServiceError,
    NotFoundError,
    ValidationError,
)

__all__ = ["DomainError", "NotFoundError", "ValidationError", "ExternalServiceError"]
