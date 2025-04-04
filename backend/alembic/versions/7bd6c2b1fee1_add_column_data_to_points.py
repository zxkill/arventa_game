"""add column data to points

Revision ID: 7bd6c2b1fee1
Revises: 6c2a940313fa
Create Date: 2024-12-20 15:51:16.553014

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7bd6c2b1fee1'
down_revision: Union[str, None] = '6c2a940313fa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE points ADD COLUMN object_id integer not null default 0;")


def downgrade() -> None:
    op.execute("ALTER TABLE points DROP COLUMN object_id;")
