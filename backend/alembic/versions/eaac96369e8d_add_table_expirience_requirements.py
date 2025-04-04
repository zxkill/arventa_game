"""add table expirience requirements

Revision ID: eaac96369e8d
Revises: 6c3da173a6e5
Create Date: 2025-01-15 14:59:51.249764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eaac96369e8d'
down_revision: Union[str, None] = '6c3da173a6e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
       CREATE TABLE item_experience_requirements (
        id SERIAL PRIMARY KEY,
        level INTEGER NOT NULL DEFAULT 1,
        experience_required  INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    op.execute("""
           CREATE TABLE player_item_progress (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users (id),
            type_item VARCHAR(30) NOT NULL, -- оружие, броня, инструмент
            type_resource VARCHAR(30) DEFAULT NULL, -- wood, skin
            current_experience INTEGER NOT NULL DEFAULT 1,
            current_level INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)

def downgrade() -> None:
    op.execute("DROP TABLE item_experience_requirements;")
    op.execute("DROP TABLE player_item_progress;")
