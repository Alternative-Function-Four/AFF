"""Add home location fields to preferences."""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_preference_home_location"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "preferences",
        sa.Column("home_lat", sa.Float(), nullable=False, server_default="1.3521"),
    )
    op.add_column(
        "preferences",
        sa.Column("home_lng", sa.Float(), nullable=False, server_default="103.8198"),
    )
    op.add_column(
        "preferences",
        sa.Column(
            "home_address",
            sa.String(length=255),
            nullable=False,
            server_default="Singapore",
        ),
    )


def downgrade() -> None:
    op.drop_column("preferences", "home_address")
    op.drop_column("preferences", "home_lng")
    op.drop_column("preferences", "home_lat")

