# Imagen de la aplicación. Basada en la imagen oficial de Playwright para
# Python 3.13, que ya incluye Chromium y sus dependencias del sistema.
FROM mcr.microsoft.com/playwright/python:v1.48.0-noble

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Instalar dependencias primero para aprovechar la caché de capas.
COPY pyproject.toml ./
COPY README.md ./
RUN pip install --upgrade pip && pip install ".[dev]"

# Código de la aplicación.
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY scripts ./scripts

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
