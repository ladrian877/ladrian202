"""Inserta datos de ejemplo en la base de datos (para demos y pruebas manuales).

Uso:
    python -m scripts.seed
"""

from __future__ import annotations

from app.config.logging import configure_logging, get_logger
from app.database.session import get_session_factory
from app.models.company import Company
from app.models.search_query import SearchQuery

logger = get_logger("scripts.seed")

_SAMPLE = [
    ("Clínica Dental Sonrisa", "https://example-dental.com", "dentistas", 4.6, 210),
    ("Restaurante La Plaza", None, "restaurantes", 4.2, 89),
    ("Gimnasio PowerFit", "https://example-gym.com", "gimnasios", 4.0, 54),
]


def main() -> None:
    configure_logging(level="INFO")
    session = get_session_factory()()
    try:
        search = SearchQuery(category="varios", city="Madrid", results_count=len(_SAMPLE))
        session.add(search)
        session.flush()
        for name, website, category, rating, reviews in _SAMPLE:
            session.add(
                Company(
                    name=name,
                    website=website,
                    category=category,
                    city="Madrid",
                    rating=rating,
                    reviews_count=reviews,
                    search_query_id=search.id,
                    source="seed",
                )
            )
        session.commit()
        logger.info("Insertadas %d empresas de ejemplo", len(_SAMPLE))
    finally:
        session.close()


if __name__ == "__main__":
    main()
