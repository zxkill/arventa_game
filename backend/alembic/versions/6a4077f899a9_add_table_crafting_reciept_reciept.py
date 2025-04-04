"""add table crafting reciept + reciept

Revision ID: 6a4077f899a9
Revises: 7e497b11ddbd
Create Date: 2025-01-07 08:11:04.707825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6a4077f899a9'
down_revision: Union[str, None] = '7e497b11ddbd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE crafting_recipes (
            id SERIAL PRIMARY KEY,
            item_id INTEGER NOT NULL REFERENCES items (id),    -- Создаваемый предмет
            quantity_crafting_item INTEGER NOT NULL DEFAULT 1,    -- 
            materials_required JSONB NOT NULL, -- Материалы и их количество в формате JSON
            crafting_time INTEGER NOT NULL,    -- Время крафта в секундах
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    # op.execute("""
    #         INSERT INTO crafting_recipes (item_id, materials_required, crafting_time) VALUES
    #             (10, '{"resources":[{"resource_id": 1, "count":5}]}', 30),
    #             (6, '{"resources":[{"resource_id": 1, "count":4}]}', 30),
    #             (7, '{"resources":[{"resource_id": 1, "count":4}]}', 30),
    #             (8, '{"resources":[{"resource_id": 1, "count":2}, {"resource_id":2,"count":2}]}', 40),
    #             (11, '{"resources":[{"resource_id": 1, "count":5}, {"resource_id":2,"count":5}]}', 60);
    #     """)


def downgrade() -> None:
    op.execute("DROP TABLE crafting_recipes;")
