"""Fix bug in title_abstract indexation

Revision ID: 159a5154362b
Revises: 73112a361617
Create Date: 2017-09-18 18:00:26.055335

"""
from alembic import op
import sqlalchemy as sa
from gargantext.util.alembic import ReplaceableObject


# revision identifiers, used by Alembic.
revision = '159a5154362b'
down_revision = '73112a361617'
branch_labels = None
depends_on = None


title_abstract_insert = ReplaceableObject(
    'title_abstract_insert',
    'BEFORE INSERT',
    'nodes',
    """FOR EACH ROW
       WHEN (NEW.hyperdata::text <> '{}'::text)
       EXECUTE PROCEDURE title_abstract_update_trigger()"""
)


title_abstract_update = ReplaceableObject(
    'title_abstract_update',
    'BEFORE UPDATE OF hyperdata',
    'nodes',
    """FOR EACH ROW
       WHEN ((OLD.hyperdata ->> 'title', OLD.hyperdata ->> 'abstract')
             IS DISTINCT FROM
             (NEW.hyperdata ->> 'title', NEW.hyperdata ->> 'abstract'))
       EXECUTE PROCEDURE title_abstract_update_trigger()"""
)


def upgrade():
    op.replace_trigger(title_abstract_insert, replaces="73112a361617.title_abstract_insert")
    op.replace_trigger(title_abstract_update, replaces="73112a361617.title_abstract_update")

    # Manually re-build index
    op.execute("UPDATE nodes SET title_abstract = to_tsvector('english', (hyperdata ->> 'title') || ' ' || (hyperdata ->> 'abstract')) WHERE typename=4")


def downgrade():
    # Won't unfix the bug !
    pass
