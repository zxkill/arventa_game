"""add table feedback

Revision ID: 4b3d11111045
Revises: db552187e780
Create Date: 2025-01-11 15:42:32.312604

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '4b3d11111045'
down_revision: Union[str, None] = 'db552187e780'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE feedback (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users (id), 
            title varchar(255) NOT NULL,
            description TEXT NOT NULL ,
            created_at TIMESTAMP DEFAULT now()
        );
    """)

def downgrade() -> None:
    op.execute("DROP TABLE feedback;")
