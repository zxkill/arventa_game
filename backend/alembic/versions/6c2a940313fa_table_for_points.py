"""table for points

Revision ID: 6c2a940313fa
Revises: afd8e455af04
Create Date: 2024-12-18 15:19:57.495802

"""
from typing import Sequence, Union

from geoalchemy2 import Geography

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '6c2a940313fa'
down_revision: Union[str, None] = 'afd8e455af04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Добавляем поддержку PostGIS (если не включено)
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # Создаем таблицу
    op.create_table(
        'points',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('type', sa.String, nullable=False),
        sa.Column('coordinates', Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('points')
