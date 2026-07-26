#!/usr/bin/env bash
# Punto de entrada del contenedor de la aplicación.
# Aplica las migraciones antes de arrancar el servidor.
set -euo pipefail

echo "==> Aplicando migraciones de base de datos..."
alembic upgrade head

echo "==> Iniciando aplicación..."
exec "$@"
