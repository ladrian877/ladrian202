"""Esquema inicial

Revision ID: 0001
Revises:
Create Date: 2026-07-26

Crea todas las tablas del dominio: búsquedas, empresas, análisis, scores,
informes de IA, emails generados y logs de actividad.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "search_queries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(length=255), nullable=False),
        sa.Column("city", sa.String(length=255), nullable=False),
        sa.Column("neighborhood", sa.String(length=255), nullable=True),
        sa.Column("params", sa.JSON(), nullable=False),
        sa.Column("results_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_search_queries_category", "search_queries", ["category"])
    op.create_index("ix_search_queries_city", "search_queries", ["city"])

    op.create_table(
        "companies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("place_id", sa.String(length=255), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("search_query_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=255), nullable=True),
        sa.Column("neighborhood", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("website", sa.String(length=1000), nullable=True),
        sa.Column("category", sa.String(length=255), nullable=True),
        sa.Column("hours", sa.JSON(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("reviews_count", sa.Integer(), nullable=True),
        sa.Column("google_maps_url", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["search_query_id"], ["search_queries.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("place_id", name="uq_companies_place_id"),
    )
    op.create_index("ix_companies_city", "companies", ["city"])
    op.create_index("ix_companies_category", "companies", ["category"])
    op.create_index("ix_companies_city_category", "companies", ["city", "category"])

    op.create_table(
        "website_analyses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("https", sa.Boolean(), nullable=True),
        sa.Column("responsive", sa.Boolean(), nullable=True),
        sa.Column("cms", sa.String(length=100), nullable=True),
        sa.Column("framework", sa.String(length=100), nullable=True),
        sa.Column("google_analytics", sa.Boolean(), nullable=True),
        sa.Column("google_tag_manager", sa.Boolean(), nullable=True),
        sa.Column("meta_pixel", sa.Boolean(), nullable=True),
        sa.Column("favicon", sa.Boolean(), nullable=True),
        sa.Column("sitemap", sa.Boolean(), nullable=True),
        sa.Column("robots_txt", sa.Boolean(), nullable=True),
        sa.Column("contact_form", sa.Boolean(), nullable=True),
        sa.Column("whatsapp", sa.Boolean(), nullable=True),
        sa.Column("social_links", sa.JSON(), nullable=True),
        sa.Column("has_blog", sa.Boolean(), nullable=True),
        sa.Column("load_time_ms", sa.Integer(), nullable=True),
        sa.Column("performance_score", sa.Float(), nullable=True),
        sa.Column("unoptimized_images", sa.Integer(), nullable=True),
        sa.Column("meta_title", sa.String(length=1000), nullable=True),
        sa.Column("meta_description", sa.Text(), nullable=True),
        sa.Column("h1", sa.JSON(), nullable=True),
        sa.Column("h2", sa.JSON(), nullable=True),
        sa.Column("seo_findings", sa.JSON(), nullable=True),
        sa.Column("accessibility_findings", sa.JSON(), nullable=True),
        sa.Column("broken_links", sa.JSON(), nullable=True),
        sa.Column("raw", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_website_analyses_company_id", "website_analyses", ["company_id"])

    op.create_table(
        "lead_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.Integer(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=True),
        sa.Column("breakdown", sa.JSON(), nullable=False),
        sa.Column("config_version", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["website_analyses.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_lead_scores_company_id", "lead_scores", ["company_id"])
    op.create_index("ix_lead_scores_company_created", "lead_scores", ["company_id", "created_at"])

    op.create_table(
        "ai_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("weaknesses", sa.JSON(), nullable=False),
        sa.Column("opportunities", sa.JSON(), nullable=False),
        sa.Column("recommendations", sa.JSON(), nullable=False),
        sa.Column("suggested_services", sa.JSON(), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ai_reports_company_id", "ai_reports", ["company_id"])

    op.create_table(
        "generated_emails",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("subject", sa.String(length=500), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("tone", sa.String(length=50), nullable=True),
        sa.Column("language", sa.String(length=10), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_generated_emails_company_id", "generated_emails", ["company_id"])

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("level", sa.String(length=20), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_activity_logs_entity_type", "activity_logs", ["entity_type"])
    op.create_index("ix_activity_logs_entity_id", "activity_logs", ["entity_id"])


def downgrade() -> None:
    op.drop_table("activity_logs")
    op.drop_table("generated_emails")
    op.drop_table("ai_reports")
    op.drop_table("lead_scores")
    op.drop_table("website_analyses")
    op.drop_table("companies")
    op.drop_table("search_queries")
