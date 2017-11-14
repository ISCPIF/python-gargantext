"""Use current_user_id() as default nodes.user_id

Revision ID: 291289b47bad
Revises: 4db5dcbe4bc7
Create Date: 2017-10-09 14:58:12.992106

"""
from alembic import op
import sqlalchemy as sa
import gargantext


# revision identifiers, used by Alembic.
revision = '291289b47bad'
down_revision = '4db5dcbe4bc7'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('nodes', 'user_id',
               existing_type=sa.INTEGER(),
               server_default=sa.text('current_user_id()'),
               existing_nullable=False)


def downgrade():
    op.alter_column('nodes', 'user_id',
               existing_type=sa.INTEGER(),
               server_default=None,
               existing_nullable=False)
