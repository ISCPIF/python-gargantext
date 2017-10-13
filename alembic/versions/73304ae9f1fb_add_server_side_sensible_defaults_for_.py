"""Add server side sensible defaults for nodes

Revision ID: 73304ae9f1fb
Revises: 159a5154362b
Create Date: 2017-10-05 14:17:58.326646

"""
from alembic import op
import sqlalchemy as sa
import gargantext
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '73304ae9f1fb'
down_revision = '159a5154362b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE nodes SET date = CURRENT_TIMESTAMP WHERE date IS NULL")
    op.execute("UPDATE nodes SET hyperdata = '{}'::jsonb WHERE hyperdata IS NULL")
    op.execute("UPDATE nodes SET name = '' WHERE name IS NULL")
    op.execute("DELETE FROM nodes WHERE typename IS NULL")
    op.execute("DELETE FROM nodes WHERE user_id IS NULL")

    op.alter_column('nodes', 'date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               server_default=sa.text('CURRENT_TIMESTAMP'),
               nullable=False)
    op.alter_column('nodes', 'hyperdata',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               server_default=sa.text("'{}'::jsonb"),
               nullable=False)
    op.alter_column('nodes', 'name',
               existing_type=sa.VARCHAR(length=255),
               server_default='',
               nullable=False)
    op.alter_column('nodes', 'typename',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('nodes', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=False)


def downgrade():
    op.alter_column('nodes', 'user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('nodes', 'typename',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('nodes', 'name',
               existing_type=sa.VARCHAR(length=255),
               server_default=None,
               nullable=True)
    op.alter_column('nodes', 'hyperdata',
               existing_type=postgresql.JSONB(astext_type=sa.Text()),
               server_default=None,
               nullable=True)
    op.alter_column('nodes', 'date',
               existing_type=postgresql.TIMESTAMP(timezone=True),
               server_default=None,
               nullable=True)
