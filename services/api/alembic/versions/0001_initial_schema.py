"""Initial schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True, unique=True),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "sessions",
        sa.Column("token", sa.String(length=128), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "preferences",
        sa.Column("user_id", sa.String(length=36), primary_key=True),
        sa.Column("preferred_categories", sa.JSON(), nullable=False),
        sa.Column("preferred_subcategories", sa.JSON(), nullable=False),
        sa.Column("budget_mode", sa.String(length=32), nullable=False),
        sa.Column("preferred_distance_km", sa.Float(), nullable=False),
        sa.Column("active_days", sa.String(length=32), nullable=False),
        sa.Column("preferred_times", sa.JSON(), nullable=False),
        sa.Column("anti_preferences", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "sources",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=512), nullable=False, unique=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("access_method", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("policy_risk_score", sa.Integer(), nullable=False),
        sa.Column("quality_score", sa.Integer(), nullable=False),
        sa.Column("crawl_frequency_minutes", sa.Integer(), nullable=False),
        sa.Column("terms_url", sa.String(length=512), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=128), nullable=False),
        sa.Column("subcategory", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("venue_name", sa.String(length=255), nullable=True),
        sa.Column("venue_address", sa.String(length=255), nullable=True),
        sa.Column("price_min", sa.Float(), nullable=True),
        sa.Column("price_max", sa.Float(), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "event_occurrences",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("datetime_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("datetime_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "event_provenance",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "raw_events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("external_event_id", sa.String(length=255), nullable=True),
        sa.Column("payload_ref", sa.String(length=255), nullable=False),
        sa.Column("raw_title", sa.String(length=255), nullable=True),
        sa.Column("raw_date_or_schedule", sa.String(length=255), nullable=True),
        sa.Column("raw_location", sa.String(length=255), nullable=True),
        sa.Column("raw_description", sa.Text(), nullable=True),
        sa.Column("raw_price", sa.String(length=64), nullable=True),
        sa.Column("raw_url", sa.String(length=512), nullable=True),
        sa.Column("raw_media_url", sa.String(length=512), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], ondelete="SET NULL"),
    )

    op.create_table(
        "event_source_links",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("raw_event_id", sa.String(length=36), nullable=False),
        sa.Column("source_id", sa.String(length=36), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("external_event_id", sa.String(length=255), nullable=True),
        sa.Column("merge_confidence", sa.Float(), nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "interactions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("signal", sa.String(length=64), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("context_hash", sa.String(length=64), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("notify_immediately", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "notifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=36), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "ingestion_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("normalization_low_confidence_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_parse_failures_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dedup_skip_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dedup_merge_sources_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("dedup_create_new_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "ingestion_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("service", sa.String(length=64), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("event_id", sa.String(length=36), nullable=True),
        sa.Column("message", sa.String(length=255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )

    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("source_ids", sa.JSON(), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("run_id", sa.String(length=64), nullable=False),
        sa.Column("created_events", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("merge_actions", sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("ingestion_jobs")
    op.drop_table("ingestion_logs")
    op.drop_table("ingestion_metrics")
    op.drop_table("notifications")
    op.drop_table("recommendations")
    op.drop_table("interactions")
    op.drop_table("event_source_links")
    op.drop_table("raw_events")
    op.drop_table("event_provenance")
    op.drop_table("event_occurrences")
    op.drop_table("events")
    op.drop_table("sources")
    op.drop_table("preferences")
    op.drop_table("sessions")
    op.drop_table("users")
