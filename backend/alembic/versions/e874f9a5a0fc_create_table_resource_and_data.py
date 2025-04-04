"""create table resource and data

Revision ID: e874f9a5a0fc
Revises: cdf1bc4a6617
Create Date: 2024-12-31 09:56:44.773627

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e874f9a5a0fc'
down_revision: Union[str, None] = 'cdf1bc4a6617'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
       CREATE TABLE resources (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        type VARCHAR(30) NOT NULL DEFAULT 'wood',
        harvest_time_seconds INT NOT NULL,
        cooldown_seconds INT NOT NULL,
        loot JSONB NOT NULL,
        description TEXT
        );
    """)

def downgrade() -> None:
    op.execute("DROP TABLE resources;")
