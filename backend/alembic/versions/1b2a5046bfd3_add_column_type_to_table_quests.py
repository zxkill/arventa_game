"""add column type to table quests

Revision ID: 1b2a5046bfd3
Revises: 109118a2d876
Create Date: 2024-12-28 12:11:26.954454

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b2a5046bfd3'
down_revision: Union[str, None] = '109118a2d876'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE quests ADD COLUMN type varchar(4) NOT NULL DEFAULT 'main'")
    op.execute("ALTER TABLE quests ADD COLUMN sort integer NOT NULL DEFAULT 1")


def downgrade() -> None:
    op.execute("ALTER TABLE quests DROP COLUMN type;")
    op.execute("ALTER TABLE quests DROP COLUMN sort;")
