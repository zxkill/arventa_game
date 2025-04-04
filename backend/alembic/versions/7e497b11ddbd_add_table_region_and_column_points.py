"""add table region and column points

Revision ID: 7e497b11ddbd
Revises: 506358fd8691
Create Date: 2025-01-06 04:58:16.308302

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7e497b11ddbd'
down_revision: Union[str, None] = '506358fd8691'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE regions (
        id SERIAL PRIMARY KEY,
        name VARCHAR NOT NULL,
        density INTEGER NOT NULL DEFAULT 1, -- Плотность (точек на км²)
        top_left GEOGRAPHY(Point, 4326) NOT NULL,    -- Верхняя левая точка квадрата
        bottom_right GEOGRAPHY(Point, 4326) NOT NULL -- Нижняя правая точка квадрата
    );
    """)
    op.execute("""
    ALTER TABLE points
    ADD COLUMN region_id INTEGER,
    ADD CONSTRAINT fk_region FOREIGN KEY (region_id) REFERENCES regions (id);
    """)

def downgrade() -> None:
    op.execute("ALTER TABLE points DROP COLUMN region_id;")
    op.execute("DROP TABLE regions;")
