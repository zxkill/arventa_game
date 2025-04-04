"""add column cooldown to monsters

Revision ID: 506358fd8691
Revises: e874f9a5a0fc
Create Date: 2025-01-05 08:32:25.540281

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '506358fd8691'
down_revision: Union[str, None] = 'e874f9a5a0fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE monsters ADD COLUMN cooldown_seconds integer NOT NULL DEFAULT 60")


def downgrade() -> None:
    op.execute("ALTER TABLE monsters DROP COLUMN cooldown_seconds;")
