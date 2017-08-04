"""Fix issue with Node.hyperdata index

Revision ID: bedce47c9e34
Revises: 08230100f262
Create Date: 2017-07-10 11:30:59.168190

"""
from alembic import op
import sqlalchemy as sa
import gargantext


# revision identifiers, used by Alembic.
revision = 'bedce47c9e34'
down_revision = '08230100f262'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index('nodes_hyperdata_idx', table_name='nodes')
    op.create_index('nodes_hyperdata_idx', 'nodes', ['hyperdata'], unique=False, postgresql_using="gin")


def downgrade():
    # We won't unfix the bug when downgrading...
    pass
