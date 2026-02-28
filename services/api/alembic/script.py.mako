"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision}
Create Date: ${create_date}
"""

from alembic import op
import sqlalchemy as sa

${imports if imports else ""}


${upgrades if upgrades else ""}


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
