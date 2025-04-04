"""add columns to user_profile

Revision ID: 7f9bdac7abc5
Revises: 4b3d11111045
Create Date: 2025-01-12 15:04:37.350841

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7f9bdac7abc5'
down_revision: Union[str, None] = '4b3d11111045'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE avatars (
            id SERIAL PRIMARY KEY,
            title varchar(255) NOT NULL,
            description TEXT NOT NULL,
            url varchar(255) NOT NULL,
            created_at TIMESTAMP DEFAULT now()
        );
    """)

    op.execute("""
    ALTER TABLE user_profiles DROP COLUMN avatar_url;
    ALTER TABLE user_profiles ADD COLUMN name varchar(100) DEFAULT NULL;
    ALTER TABLE user_profiles ADD COLUMN birthday date DEFAULT NULL;
    ALTER TABLE user_profiles ADD COLUMN avatar_id INTEGER REFERENCES avatars (id);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE avatars;")
    op.execute("""
    ALTER TABLE user_profiles DROP COLUMN name;
    ALTER TABLE user_profiles DROP COLUMN birthday;
    ALTER TABLE user_profiles DROP COLUMN avatar_id;
    """)
