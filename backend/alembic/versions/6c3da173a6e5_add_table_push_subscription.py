"""add table push_subscription

Revision ID: 6c3da173a6e5
Revises: 7f9bdac7abc5
Create Date: 2025-01-14 07:50:51.694331

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c3da173a6e5'
down_revision: Union[str, None] = '7f9bdac7abc5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE push_subscriptions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users (id),
            endpoint TEXT NOT NULL,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT now()
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE push_subscriptions;")
