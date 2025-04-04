"""add silver column to users

Revision ID: aef3986ec70a
Revises: 6da07a00599e
Create Date: 2024-12-26 12:39:59.428182

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'aef3986ec70a'
down_revision: Union[str, None] = '6da07a00599e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN silver INTEGER DEFAULT 0;")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN silver;")
