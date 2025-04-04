"""items user items

Revision ID: a2a2224a81c9
Revises: 7bd6c2b1fee1
Create Date: 2024-12-24 11:44:03.477901

"""
from typing import Sequence, Union

from sqlalchemy.dialects.postgresql import JSONB

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a2a2224a81c9'
down_revision: Union[str, None] = '7bd6c2b1fee1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('items')
    op.create_table(
        'items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('rarity', sa.String(50)),
        sa.Column('damage', sa.Integer, default=0),
        sa.Column('armor', sa.Integer, default=0),
        sa.Column('effect', JSONB),
        sa.Column('resource_type', sa.String(50)),
        sa.Column('weight', sa.Float, default=0),
        sa.Column('price', sa.Integer, default=0),
        sa.Column('is_stackable', sa.Boolean, default=False),
        sa.Column('stack_size', sa.Integer, default=1),
        sa.Column('description', sa.String),
        sa.Column('geometry', sa.String),  # Placeholder for PostGIS
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )

    op.execute(
        """
        INSERT INTO items (name, type, rarity, damage, armor, effect, resource_type, weight, price, is_stackable, stack_size, description)
    VALUES \
    ('Меч Новичка', 'Оружие', 'Обычный', 10, 0, '{"speed_bonus": 2}', NULL, 2.5, 50, FALSE, 1,
     'Простой меч для новичков.'), \
    ('Кожаный Нагрудник', 'Броня', 'Обычный', 0, 10, '{"endurance_bonus": 2}', NULL, 3.0, 30, FALSE, 1,
     'Легкий нагрудник из кожи.'), \
    ('Кольцо Мудрости', 'Аксессуар', 'Редкий', 0, 0, '{"intelligence_bonus": 5}', NULL, 0.1, 100, FALSE, 1,
     'Древнее кольцо, повышающее интеллект.'), \
    ('Древесина', 'Ресурс', 'Обычный', 0, 0, NULL, 'Дерево', 1.0, 5, TRUE, 50, 'Основной материал для строительства.'), \
    ('Сапфир', 'Ресурс', 'Эпический', 0, 0, NULL, 'Камень', 0.2, 200, TRUE, 10,
     'Драгоценный камень, используемый для улучшения.'), \
    ('Зачарованная Рукоять', 'Улучшение', 'Редкий', 0, 0, '{"damage_bonus": 5}', NULL, 0.5, 150, FALSE, 1,
     'Рукоять для улучшения оружия.');
     """)

    # Create 'user_items' table
    op.create_table(
        'user_items',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('item_id', sa.Integer, sa.ForeignKey('items.id'), nullable=False),
        sa.Column('durability', sa.Integer, default=100),
        sa.Column('modifications', JSONB),
        sa.Column('quantity', sa.Integer, default=1),
        sa.Column('is_equipped', sa.Boolean, default=False),
        sa.Column('acquired_at', sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )

    op.execute(
        """
        -- Пример 1: Добавление экипированного меча с индивидуальной прочностью и модификацией
        INSERT INTO user_items (user_id, item_id, durability, modifications, is_equipped)
        VALUES
        (1, 1, 85, '{"sharpness_bonus": 5}', TRUE);
        
        -- Пример 2: Добавление ресурса (20 единиц древесины)
        INSERT INTO user_items (user_id, item_id, quantity)
        VALUES
        (1, 4, 20);
        
        -- Пример 3: Добавление кольца с улучшением (плюс интеллект) и стандартной прочностью
        INSERT INTO user_items (user_id, item_id, modifications)
        VALUES
        (1, 3, '{"intelligence_bonus": 2}');
     """)


def downgrade() -> None:
    op.drop_table('user_items')
    op.drop_table('items')
