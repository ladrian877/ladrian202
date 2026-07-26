# Plataforma de Prospección Inteligente

Sistema modular para agencias de marketing que, dado un **tipo de negocio + ciudad + barrio**,
encuentra empresas, analiza su presencia digital, puntúa el lead (0-100), genera un informe de
oportunidades con IA y redacta un email de contacto personalizado.

> Estado: en construcción por fases. Este README se ampliará al completar cada fase.

## Arquitectura

Clean Architecture con puertos y adaptadores: la lógica de negocio (`app/services`) depende de
*interfaces* (`Protocol`), no de implementaciones concretas (Google Places, OpenAI, Playwright, BD).

```
app/
├── api/          # Capa HTTP (FastAPI): routers y dependencias
├── config/       # Configuración central (pydantic-settings) y logging
├── core/         # Errores de dominio y tipos base
├── database/     # Engine y sesiones SQLAlchemy
├── models/       # Modelos ORM (tablas)
├── schemas/      # DTOs Pydantic
├── repositories/ # Acceso a datos (patrón Repository)
├── services/     # Casos de uso (orquestación)
├── scrapers/     # Adaptadores de fuentes externas (Places, fetch web)
├── analyzers/    # Análisis web (una estrategia por dimensión) + pipeline
├── scoring/      # Puntuación de lead configurable
├── ai/           # Proveedor LLM abstracto + prompts
├── tasks/        # Ejecución en segundo plano (interfaz enchufable a Celery)
└── utils/        # Reintentos, rate limiting, caché, HTTP
```

## Requisitos

- Python 3.11+ (imagen Docker: 3.13)
- PostgreSQL 16 (vía Docker)
- (Opcional) Claves de Google Places y OpenAI

## Puesta en marcha (Docker)

```bash
cp .env.example .env      # rellena las claves si las tienes
docker compose up --build
```

La API queda en `http://localhost:8000` con documentación en `/docs`.
El contenedor aplica las migraciones (`alembic upgrade head`) al arrancar.

## Puesta en marcha (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Levanta solo la BD:
docker compose up -d db
alembic upgrade head
uvicorn app.main:app --reload
```

## Desarrollo

```bash
pytest              # tests (SQLite en memoria, sin red)
ruff check app      # linting
mypy app            # tipado estático
```

## Configuración

Toda la configuración vive en variables de entorno (ver `.env.example`). Puntos destacados:

- `DATABASE_URL`: conexión PostgreSQL (driver `psycopg` v3).
- `GOOGLE_PLACES_API_KEY`: si está vacío, en desarrollo se usa un proveedor de datos *fake*.
- `LLM_PROVIDER` / `OPENAI_API_KEY`: si no hay clave, la IA degrada a un proveedor determinista (`null`).

## Escalabilidad

El diseño contempla el crecimiento a miles de empresas:

- **Colas**: el `TaskRunner` abstrae la ejecución en segundo plano; hoy usa `asyncio`, mañana
  Celery/arq + Redis (servicio ya previsto y comentado en `docker-compose.yml`) sin refactor.
- **Rate limiting** por proveedor (`app/utils/rate_limiter.py`) y **reintentos con backoff**
  (`app/utils/retry.py`) en toda llamada externa.
- **Caché** con interfaz sustituible por Redis (`app/utils/cache.py`).
- **Nuevas fuentes de datos**: basta un adaptador que implemente `PlacesProvider`.

## Licencia

MIT.
