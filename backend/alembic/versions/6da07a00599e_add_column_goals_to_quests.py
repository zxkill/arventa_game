"""add column goals to quests

Revision ID: 6da07a00599e
Revises: a2a2224a81c9
Create Date: 2024-12-25 03:43:06.755902

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6da07a00599e'
down_revision: Union[str, None] = 'a2a2224a81c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    ALTER TABLE quests ADD COLUMN conditions JSONB;
    ALTER TABLE quests ADD COLUMN expires_at timestamp;
    ALTER TABLE quests ADD COLUMN completed_description TEXT DEFAULT '';
    ALTER TABLE user_quests ADD COLUMN progress JSONB;
    """)


def downgrade() -> None:
    op.execute("""
    ALTER TABLE quests DROP COLUMN conditions;
    ALTER TABLE quests DROP COLUMN expires_at;
    ALTER TABLE user_quests DROP COLUMN progress;
    """)
