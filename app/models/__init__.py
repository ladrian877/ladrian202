"""Modelos ORM de SQLAlchemy.

Importar aquí todos los modelos garantiza que estén registrados en
``Base.metadata`` cuando Alembic autogenera migraciones.
"""

from app.models.activity_log import ActivityLog
from app.models.ai_report import AIReport
from app.models.base import Base
from app.models.company import Company
from app.models.generated_email import GeneratedEmail
from app.models.lead_score import LeadScore
from app.models.search_query import SearchQuery
from app.models.website_analysis import WebsiteAnalysis

__all__ = [
    "Base",
    "Company",
    "SearchQuery",
    "WebsiteAnalysis",
    "LeadScore",
    "AIReport",
    "GeneratedEmail",
    "ActivityLog",
]
