"""Merge migration heads

Revision ID: 0b4e3b012857
Revises: 4a479137de27, b7c3d1e94f02
Create Date: 2026-08-07 16:50:55.430220

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b4e3b012857'
down_revision = ('4a479137de27', 'b7c3d1e94f02')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
