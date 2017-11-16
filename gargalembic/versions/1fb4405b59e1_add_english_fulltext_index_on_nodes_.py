"""Add english fulltext index on Nodes.hyperdata for abstract and title

Revision ID: 1fb4405b59e1
Revises: bedce47c9e34
Create Date: 2017-09-13 16:31:36.926692

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy_utils.types import TSVectorType
from gargantext.util.alembic import ReplaceableObject


# revision identifiers, used by Alembic.
revision = '1fb4405b59e1'
down_revision = 'bedce47c9e34'
branch_labels = None
depends_on = None


title_abstract_update_trigger = ReplaceableObject(
    'title_abstract_update_trigger()',
    """
RETURNS trigger AS $$
begin
  new.title_abstract := to_tsvector('english', (new.hyperdata ->> 'title') || ' ' || (new.hyperdata ->> 'abstract'));
  return new;
end
$$ LANGUAGE plpgsql;
    """
)


title_abstract_update = ReplaceableObject(
    'title_abstract_update',
    'BEFORE INSERT OR UPDATE',
    'nodes',
    'FOR EACH ROW EXECUTE PROCEDURE title_abstract_update_trigger()'
)


def upgrade():
    op.add_column('nodes', sa.Column('title_abstract', TSVectorType))
    op.create_sp(title_abstract_update_trigger)
    op.create_trigger(title_abstract_update)

    # Initialize index with already existing data
    op.execute('UPDATE nodes SET hyperdata = hyperdata');


def downgrade():
    op.drop_trigger(title_abstract_update)
    op.drop_sp(title_abstract_update_trigger)
    op.drop_column('nodes', 'title_abstract')
