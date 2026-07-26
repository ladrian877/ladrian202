# Plataforma de Prospección Inteligente

Sistema modular para agencias de marketing que, dado un **tipo de negocio + ciudad + barrio**,
encuentra empresas, analiza su presencia digital, puntúa el lead (0-100), genera un informe de
oportunidades con IA y redacta un email de contacto personalizado.

Construido con **FastAPI + SQLAlchemy + PostgreSQL + Playwright + OpenAI**, siguiendo Clean
Architecture, SOLID, tipado completo (`mypy --strict`), logging estructurado y configuración por
entorno.

---

## Índice

- [Arquitectura](#arquitectura)
- [Flujo funcional](#flujo-funcional)
- [Requisitos](#requisitos)
- [Puesta en marcha (Docker)](#puesta-en-marcha-docker)
- [Puesta en marcha (local)](#puesta-en-marcha-local)
- [API](#api)
- [Ejemplos de uso](#ejemplos-de-uso)
- [Configuración](#configuración)
- [Scoring configurable](#scoring-configurable)
- [Desarrollo y calidad](#desarrollo-y-calidad)
- [Escalabilidad](#escalabilidad)

---

## Arquitectura

Clean Architecture con puertos y adaptadores: la lógica de negocio (`app/services`) depende de
*interfaces* (`Protocol`), no de implementaciones concretas (Google Places, OpenAI, Playwright, BD).
Los adaptadores se inyectan vía `app/api/deps.py`, lo que hace el sistema testeable sin red y fácil
de extender.

```
app/
├── api/          # Capa HTTP (FastAPI): routers v1 y dependencias
├── config/       # Configuración central (pydantic-settings) y logging
├── core/         # Errores de dominio
├── database/     # Engine y sesiones SQLAlchemy
├── models/       # Modelos ORM (companies, analyses, scores, reports, emails, logs)
├── schemas/      # DTOs Pydantic
├── repositories/ # Acceso a datos (patrón Repository)
├── services/     # Casos de uso (prospección, análisis, scoring, informe, email, export)
├── scrapers/     # Adaptadores externos: Google Places + WebFetcher híbrido
├── analyzers/    # Análisis web: una estrategia por dimensión + pipeline
├── scoring/      # Puntuación de lead configurable (reglas + pesos)
├── ai/           # LLMProvider abstracto (OpenAI / null), prompts e insights
├── tasks/        # Ejecución en segundo plano (interfaz enchufable a Celery)
└── utils/        # Reintentos, rate limiting, caché, HTTP
```

## Flujo funcional

```
Búsqueda (Places) → Persistencia → Análisis web → Scoring → Informe IA → Email IA → Exportación
```

1. **Búsqueda**: Google Places (o proveedor *fake* sin API key) por categoría/ciudad/barrio.
2. **Análisis web**: HTTPS, responsive, CMS/framework, GA/GTM/Meta Pixel, favicon, sitemap,
   robots.txt, formulario, WhatsApp, redes, blog, velocidad, imágenes sin optimizar, SEO
   (title/description/H1/H2), accesibilidad y enlaces rotos.
3. **Scoring**: 0-100 según las carencias detectadas, con pesos configurables.
4. **Informe IA**: fortalezas, debilidades, oportunidades, recomendaciones, servicios a vender y
   prioridad del lead.
5. **Email IA**: mensaje personalizado que menciona problemas reales y ofrece soluciones.
6. **Exportación**: CSV, Excel o JSON.

## Requisitos

- Python 3.11+ (imagen Docker: 3.13)
- PostgreSQL 16 (vía Docker)
- (Opcional) `GOOGLE_PLACES_API_KEY` y `OPENAI_API_KEY` — sin ellas el sistema funciona con
  proveedores *fake*/deterministas.

## Puesta en marcha (Docker)

```bash
cp .env.example .env      # rellena las claves si las tienes
docker compose up --build
```

La API queda en `http://localhost:8000`, documentación en `/docs`. El contenedor aplica las
migraciones (`alembic upgrade head`) automáticamente al arrancar.

## Puesta en marcha (local)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
docker compose up -d db          # solo la base de datos
alembic upgrade head
uvicorn app.main:app --reload
```

## API

Todos los endpoints cuelgan de `/api/v1`. Documentación interactiva en `/docs` y `/redoc`.

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET`  | `/health` | Estado del servicio |
| `POST` | `/companies/search` | Buscar empresas (categoría/ciudad/barrio) y guardarlas |
| `GET`  | `/companies` | Listar con filtros (`city`, `category`, `min_score`, `max_score`, `has_website`) y paginación |
| `GET`  | `/companies/{id}` | Detalle de una empresa |
| `GET`  | `/companies/{id}/scores` | Historial de puntuaciones |
| `GET`  | `/companies/export?format=csv\|xlsx\|json` | Exportar (mismos filtros que el listado) |
| `POST` | `/companies/{id}/analyze` | Lanzar análisis web (asíncrono, 202) |
| `POST` | `/companies/{id}/reanalyze` | Forzar reanálisis |
| `GET`  | `/companies/{id}/analysis` | Último análisis |
| `POST` | `/companies/{id}/report` | Generar informe de oportunidades con IA |
| `GET`  | `/companies/{id}/report` | Último informe |
| `POST` | `/companies/{id}/email` | Generar email de contacto con IA |
| `GET`  | `/companies/{id}/email` | Último email |

## Ejemplos de uso

Buscar empresas:

```bash
curl -X POST http://localhost:8000/api/v1/companies/search \
  -H "Content-Type: application/json" \
  -d '{"category": "dentistas", "city": "Madrid", "neighborhood": "Centro", "max_results": 20}'
```

Analizar, puntuar, informar y generar email:

```bash
curl -X POST http://localhost:8000/api/v1/companies/1/analyze
curl      http://localhost:8000/api/v1/companies/1/analysis
curl -X POST http://localhost:8000/api/v1/companies/1/report
curl -X POST http://localhost:8000/api/v1/companies/1/email
```

Filtrar leads calientes y exportar:

```bash
curl "http://localhost:8000/api/v1/companies?min_score=70&city=Madrid"
curl -OJ "http://localhost:8000/api/v1/companies/export?format=xlsx&min_score=70"
```

Flujo completo por CLI (usa proveedores *fake*/null sin claves):

```bash
python -m scripts.run_prospection --category dentistas --city Madrid --neighborhood Centro --limit 3
python -m scripts.seed            # datos de ejemplo
```

## Configuración

Toda la configuración vive en variables de entorno (ver `.env.example`). Destacados:

- `DATABASE_URL`: conexión PostgreSQL (driver `psycopg` v3).
- `GOOGLE_PLACES_API_KEY`: vacío ⇒ proveedor *fake* de datos sintéticos (dev).
- `LLM_PROVIDER` / `OPENAI_API_KEY`: sin clave, la IA degrada a un proveedor `null` determinista
  y los servicios usan un borrador construido a partir del análisis real.
- `WEB_ANALYSIS_USE_PLAYWRIGHT`: `false` para analizar solo con `httpx` (sin render JS).
- `SCORING_CONFIG_PATH`: JSON con pesos de scoring personalizados.

## Scoring configurable

La puntuación es la proporción de carencias detectadas (ponderadas) sobre el total evaluable,
normalizada a 0-100 — a mayor score, mayor oportunidad de venta. Los pesos y los umbrales de
prioridad se ajustan sin tocar código (ver `scoring_config.example.json`):

```bash
export SCORING_CONFIG_PATH=./scoring_config.example.json
```

## Desarrollo y calidad

```bash
pytest            # tests (SQLite en memoria, sin red)
ruff check app    # linting
mypy app          # tipado estático (sin errores)
```

## Escalabilidad

El diseño contempla el crecimiento a miles de empresas:

- **Procesamiento fuera del request**: el `TaskRunner` abstrae la ejecución en segundo plano; hoy
  usa `asyncio`, mañana Celery/arq + Redis (servicio ya previsto y comentado en `docker-compose.yml`)
  sin refactor de servicios.
- **Rate limiting** por proveedor (`app/utils/rate_limiter.py`) y **reintentos con backoff**
  (`app/utils/retry.py`) en toda llamada externa.
- **Caché** con interfaz sustituible por Redis (`app/utils/cache.py`).
- **Deduplicación** por `place_id` e **índices** en BD para listados y filtros.
- **Nuevas fuentes de datos**: basta un adaptador que implemente `PlacesProvider`.
- **Análisis concurrente** acotado y aislamiento de fallos por analizador.

### Mejoras futuras

Celery/arq + Redis para colas y caché reales; PageSpeed Insights para rendimiento objetivo;
estado de tareas/webhooks; autenticación (API keys/JWT) y multi-tenant por cliente de la agencia.

## Licencia

MIT.
