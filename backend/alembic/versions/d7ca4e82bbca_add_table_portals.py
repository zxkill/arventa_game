"""add table portals

Revision ID: d7ca4e82bbca
Revises: eaac96369e8d
Create Date: 2025-01-19 14:56:14.698990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7ca4e82bbca'
down_revision: Union[str, None] = 'eaac96369e8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
       CREATE TABLE portals (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        cooldown_seconds INTEGER,
        tier INTEGER NOT NULL DEFAULT 1);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE portals;")
