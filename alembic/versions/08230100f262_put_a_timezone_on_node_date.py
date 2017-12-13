"""Put a timezone on Node.date

Revision ID: 08230100f262
Revises: 601e9d9baa4c
Create Date: 2017-07-06 13:47:10.788569

"""
from alembic import op
import sqlalchemy as sa
import gargantext


# revision identifiers, used by Alembic.
revision = '08230100f262'
down_revision = '601e9d9baa4c'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('nodes', 'date', type_=sa.DateTime(timezone=True))


def downgrade():
    op.alter_column('nodes', 'date', type_=sa.DateTime(timezone=False))
