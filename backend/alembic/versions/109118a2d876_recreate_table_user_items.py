"""recreate table user_items


Revision ID: 109118a2d876
Revises: aef3986ec70a
Create Date: 2024-12-26 12:56:38.109100

"""
from typing import Sequence, Union

from sqlalchemy.dialects.postgresql import JSONB

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '109118a2d876'
down_revision: Union[str, None] = 'aef3986ec70a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('user_items')
    op.create_table(
        'user_items',
        sa.Column('id', sa.Integer, primary_key=True),  # Уникальный идентификатор записи
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),  # Внешний ключ на users
        sa.Column('item_id', sa.Integer, sa.ForeignKey('items.id'), nullable=False),  # Внешний ключ на items
        sa.Column('durability', sa.Integer, nullable=False, server_default="1000"),  # Прочность с дефолтом
        sa.Column('modifications', JSONB, nullable=True),  # JSONB поле для модификаций
        sa.Column('quantity', sa.Integer, nullable=False, server_default="1"),  # Количество с дефолтом
        sa.Column('is_equipped', sa.Boolean, nullable=False, server_default="false"),  # Экипирован ли предмет
        sa.Column('acquired_at', sa.TIMESTAMP, server_default=sa.text("NOW()")),  # Дата получения
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.text("NOW()")),  # Дата последнего обновления
    )


def downgrade() -> None:
    pass
