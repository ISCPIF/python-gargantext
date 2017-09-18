"""Optimize title_abstract indexation

Revision ID: 73112a361617
Revises: 1fb4405b59e1
Create Date: 2017-09-15 14:14:51.737963

"""
from alembic import op
import sqlalchemy as sa
from gargantext.util.alembic import ReplaceableObject


# revision identifiers, used by Alembic.
revision = '73112a361617'
down_revision = '1fb4405b59e1'
branch_labels = None
depends_on = None


title_abstract_insert = ReplaceableObject(
    'title_abstract_insert',
    'AFTER INSERT',
    'nodes',
    """FOR EACH ROW
       WHEN (NEW.hyperdata::text <> '{}'::text)
       EXECUTE PROCEDURE title_abstract_update_trigger()"""
)


title_abstract_update = ReplaceableObject(
    'title_abstract_update',
    'AFTER UPDATE OF hyperdata',
    'nodes',
    """FOR EACH ROW
       WHEN ((OLD.hyperdata ->> 'title', OLD.hyperdata ->> 'abstract')
             IS DISTINCT FROM
             (NEW.hyperdata ->> 'title', NEW.hyperdata ->> 'abstract'))
       EXECUTE PROCEDURE title_abstract_update_trigger()"""
)


def upgrade():
    op.replace_trigger(title_abstract_update, replaces="1fb4405b59e1.title_abstract_update")
    op.create_trigger(title_abstract_insert)


def downgrade():
    op.drop_trigger(title_abstract_insert)
    op.replace_trigger(title_abstract_update, replace_with="1fb4405b59e1.title_abstract_update")
