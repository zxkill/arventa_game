"""add column setting to user_profile

Revision ID: db552187e780
Revises: 6a4077f899a9
Create Date: 2025-01-11 11:03:07.040700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db552187e780'
down_revision: Union[str, None] = '6a4077f899a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE user_profiles ADD COLUMN settings jsonb default '{}';")


def downgrade() -> None:
    op.execute("ALTER TABLE user_profiles DROP COLUMN settings;")
