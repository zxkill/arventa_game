"""add columt body_part to items table

Revision ID: 635d5ce21be4
Revises: 1b2a5046bfd3
Create Date: 2024-12-29 09:20:39.400363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '635d5ce21be4'
down_revision: Union[str, None] = '1b2a5046bfd3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE items ADD COLUMN is_equippetable boolean DEFAULT FALSE;")
    op.execute("ALTER TABLE items ADD COLUMN body_part varchar(20) DEFAULT NULL;")
    op.execute("ALTER TABLE items ADD COLUMN tier smallint DEFAULT 1;")


def downgrade() -> None:
    op.execute("ALTER TABLE items DROP COLUMN is_equippetable;")
    op.execute("ALTER TABLE items DROP COLUMN body_part;")
    op.execute("ALTER TABLE items DROP COLUMN tier;")
