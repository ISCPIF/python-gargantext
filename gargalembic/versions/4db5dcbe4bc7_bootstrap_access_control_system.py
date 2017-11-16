"""Bootstrap access control system

Revision ID: 4db5dcbe4bc7
Revises: 73304ae9f1fb
Create Date: 2017-10-06 17:23:27.765318

"""
from alembic import op
import sqlalchemy as sa
from gargantext.util.alembic import ReplaceableObject


# revision identifiers, used by Alembic.
revision = '4db5dcbe4bc7'
down_revision = '73304ae9f1fb'
branch_labels = None
depends_on = None


# Publicly exposed schema through PostgREST
api_schema = ReplaceableObject("api")
api_nodes_view = ReplaceableObject(
    "api.nodes",
    "SELECT id, typename AS type, user_id, parent_id, name, date AS created, hyperdata AS data, title_abstract FROM nodes")


# Mere mortals have 'gargantext' role, admin is 'gargantua'
gargantext_role = ReplaceableObject("gargantext", "NOLOGIN")


# PostgREST authentification system; could be used without PostgREST
authenticator_role = ReplaceableObject(
    "authenticator",
    "LOGIN NOINHERIT PASSWORD 'CHANGEME'")
anon_role = ReplaceableObject("anon", "NOLOGIN")


roles = [gargantext_role, authenticator_role, anon_role]


grants = [
    ('gargantext', 'gargantua'),

    # Enable login through PostgREST auth system for gargantua, anon and
    # gargantext
    ('gargantua, anon, gargantext', 'authenticator'),

    # Basic privileges for gargantext role
    ('CREATE, USAGE ON SCHEMA api', 'gargantext'),
    ('SELECT ON nodes', 'gargantext'),
    ('UPDATE (parent_id, name, date, hyperdata) ON nodes', 'gargantext'),
    ('INSERT ON nodes', 'gargantext'),
    ('USAGE, SELECT ON SEQUENCE nodes_id_seq', 'gargantext'),
    ('DELETE ON nodes', 'gargantext'),
]


current_user_id_sp = ReplaceableObject(
    "current_user_id()",
    """
-- Assuming JWT and claim.user_id is set to user.id at login
-- https://stackoverflow.com/questions/2082686/how-do-i-cast-a-string-to-integer-and-have-0-in-case-of-error-in-the-cast-with-p
RETURNS integer AS $$
DECLARE
    user_id INTEGER NOT NULL DEFAULT 0;
BEGIN
    BEGIN
        user_id := current_setting('request.jwt.claim.user_id')::int;
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'Invalid user_id: %. Check JWT generation.',
                     current_setting('request.jwt.claim.user_id', TRUE);
        RETURN -1;
    END;
RETURN user_id;
END;
$$ LANGUAGE plpgsql""")
stored_procedures = [current_user_id_sp]


is_owner = "COALESCE(current_user_id() = user_id, FALSE)"
is_parent_owner = "COALESCE(current_user_id() = (SELECT user_id FROM nodes n WHERE id = nodes.parent_id), FALSE)"
owner_select_policy = ReplaceableObject("owner_select", "nodes", "FOR SELECT USING (%s)" % is_owner)
owner_update_policy = ReplaceableObject("owner_update", "nodes", "FOR UPDATE USING (%s)" % is_owner)
owner_insert_policy = ReplaceableObject("owner_insert", "nodes", "FOR INSERT WITH CHECK (%s)" % is_parent_owner)
owner_delete_policy = ReplaceableObject("owner_delete", "nodes", "FOR DELETE USING (%s)" % is_parent_owner)
policies = [owner_select_policy, owner_update_policy, owner_insert_policy,
            owner_delete_policy]


def upgrade():
    op.create_schema(api_schema)

    for role in roles:
        op.create_role(role)

    op.create_view(api_nodes_view)

    for grant in grants:
        op.execute('GRANT {} TO {}'.format(*grant))

    op.execute("ALTER VIEW api.nodes OWNER TO gargantext")
    op.execute("ALTER TABLE nodes ENABLE ROW LEVEL SECURITY")

    for sp in stored_procedures:
        op.create_sp(sp)

    for policy in policies:
        op.create_policy(policy)


def downgrade():
    for policy in policies:
        op.drop_policy(policy)

    for sp in stored_procedures:
        op.drop_sp(sp)

    op.execute("ALTER TABLE nodes DISABLE ROW LEVEL SECURITY")

    for grant in grants:
        op.execute('REVOKE {} FROM {}'.format(*grant))

    op.drop_view(api_nodes_view)

    for role in roles:
        op.drop_role(role)

    op.drop_schema(api_schema)
