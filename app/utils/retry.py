"""Decoradores de reintento con backoff exponencial.

Se apoyan en ``tenacity`` para no reinventar la lógica de reintentos, pero se
exponen con una firma sencilla y valores por defecto sensatos para llamadas a
APIs externas (Places, OpenAI, fetch de webs).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from tenacity import (
    retry as _tenacity_retry,
)
from tenacity import (
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

F = TypeVar("F", bound=Callable[..., Any])


def retry(
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 16.0,
    exceptions: type[Exception] | tuple[type[Exception], ...] = Exception,
) -> Callable[[F], F]:
    """Decorador de reintentos síncronos con backoff exponencial.

    Args:
        attempts: Número máximo de intentos (incluido el primero).
        base_delay: Retardo base en segundos (2s, 4s, 8s...).
        max_delay: Retardo máximo entre intentos.
        exceptions: Excepción(es) que disparan el reintento.
    """
    return _tenacity_retry(  # type: ignore[return-value]
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=base_delay, max=max_delay),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    )


def async_retry(
    *,
    attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 16.0,
    exceptions: type[Exception] | tuple[type[Exception], ...] = Exception,
) -> Callable[[F], F]:
    """Decorador de reintentos para corutinas (misma semántica que :func:`retry`)."""
    return _tenacity_retry(  # type: ignore[return-value]
        stop=stop_after_attempt(attempts),
        wait=wait_exponential(multiplier=base_delay, max=max_delay),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    )
