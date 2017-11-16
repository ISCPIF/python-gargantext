"""Map database access control to django auth system

Revision ID: d77f0a598ad0
Revises: 291289b47bad
Create Date: 2017-10-12 15:23:40.481825

"""
from alembic import op
import sqlalchemy as sa
from gargantext.util.alembic import ReplaceableObject


# revision identifiers, used by Alembic.
revision = 'd77f0a598ad0'
down_revision = '291289b47bad'
branch_labels = None
depends_on = None


gargandmin_role = ReplaceableObject('gargandmin')


grants = [('gargandmin', 'authenticator'),
          ('gargantext', 'gargandmin')]


r = "COALESCE(current_setting('request.jwt.claim.role', TRUE), current_user)"
has_perm = "{} = 'gargantua' OR current_user_id() = user_id".format(r)
has_parent_perm = "{} = 'gargantua' OR current_user_id() = (SELECT user_id FROM nodes n WHERE id = nodes.parent_id)".format(r)
policies = {
    'owner_select': ReplaceableObject("owner_select", "nodes", "FOR SELECT USING (%s)" % has_perm),
    'owner_update': ReplaceableObject("owner_update", "nodes", "FOR UPDATE USING (%s)" % has_perm),
    'owner_insert': ReplaceableObject("owner_insert", "nodes", "FOR INSERT WITH CHECK (%s)" % has_parent_perm),
    'owner_delete': ReplaceableObject("owner_delete", "nodes", "FOR DELETE USING (%s)" % has_parent_perm),
}


def upgrade():
    op.create_role(gargandmin_role)

    for grant in grants:
        op.execute('GRANT {} TO {}'.format(*grant))

    for name, policy in policies.items():
        op.replace_policy(policy, replaces='4db5dcbe4bc7.{}_policy'.format(name))


def downgrade():
    for name, policy in policies.items():
        op.replace_policy(policy, replace_with='4db5dcbe4bc7.{}_policy'.format(name))

    for grant in grants:
        op.execute('REVOKE {} FROM {}'.format(*grant))

    op.drop_role(gargandmin_role)
