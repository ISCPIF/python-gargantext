"""Define ReplaceableObject and related operations

Implements operations to create/drop SQL objects such as views, stored
procedures and triggers that can't be "altered" but can be replaced -- hence
the name of "ReplaceableObject" class.

This recipe is directly borrowed from Alembic documentation, see
http://alembic.zzzcomputing.com/en/latest/cookbook.html#replaceable-objects

**2017-10-09** ReversibleOp.define has been added to reduce boilerplate code.

"""

from alembic.operations import Operations, MigrateOperation


__all__ = ['ReplaceableObject']


class ReplaceableObject(object):
    def __init__(self, name, *args):
        self.name = name
        self.args = args


class ReversibleOp(MigrateOperation):
    def __init__(self, target):
        self.target = target

    @classmethod
    def invoke_for_target(cls, operations, target):
        op = cls(target)
        return operations.invoke(op)

    def reverse(self):
        raise NotImplementedError()

    @classmethod
    def _get_object_from_version(cls, operations, ident):
        version, objname = ident.split(".")

        module = operations.get_context().script.get_revision(version).module
        obj = getattr(module, objname)
        return obj

    @classmethod
    def replace(cls, operations, target, replaces=None, replace_with=None):

        if replaces:
            old_obj = cls._get_object_from_version(operations, replaces)
            drop_old = cls(old_obj).reverse()
            create_new = cls(target)
        elif replace_with:
            old_obj = cls._get_object_from_version(operations, replace_with)
            drop_old = cls(target).reverse()
            create_new = cls(old_obj)
        else:
            raise TypeError("replaces or replace_with is required")

        operations.invoke(drop_old)
        operations.invoke(create_new)

    @classmethod
    def define(cls, name, cname=None, register=Operations.register_operation):
        def create(self):
            return CreateOp(self.target)

        def drop(self):
            return DropOp(self.target)

        name = name.lower()
        cname = cname or name.capitalize()

        CreateOp = type('Create%sOp' % cname, (ReversibleOp,), {'reverse': drop})
        DropOp = type('Drop%sOp' % cname, (ReversibleOp,), {'reverse': create})

        CreateOp = register('create_' + name, 'invoke_for_target')(CreateOp)
        CreateOp = register('replace_' + name, 'replace')(CreateOp)

        DropOp = register('drop_' + name, 'invoke_for_target')(DropOp)

        return (CreateOp, DropOp)


CreateViewOp,    DropViewOp    = ReversibleOp.define('view')
CreateRoleOp,    DropRoleOp    = ReversibleOp.define('role')
CreateSchemaOp,  DropSchemaOp  = ReversibleOp.define('schema')
CreateSPOp,      DropSPOp      = ReversibleOp.define('sp', 'SP')
CreateTriggerOp, DropTriggerOp = ReversibleOp.define('trigger')
CreatePolicyOp,  DropPolicyOp  = ReversibleOp.define('policy')


@Operations.implementation_for(CreateViewOp)
def create_view(operations, operation):
    operations.execute("CREATE VIEW %s AS %s" % (
        operation.target.name,
        operation.target.args[0]
    ))


@Operations.implementation_for(DropViewOp)
def drop_view(operations, operation):
    operations.execute("DROP VIEW %s" % operation.target.name)


@Operations.implementation_for(CreateRoleOp)
def create_role(operations, operation):
    args = operation.target.args
    operations.execute(
        "CREATE ROLE %s WITH %s" % (
            operation.target.name,
            args[0] if len(args) else 'NOLOGIN'
        )
    )


@Operations.implementation_for(DropRoleOp)
def drop_role(operations, operation):
    operations.execute("DROP ROLE %s" % operation.target.name)


@Operations.implementation_for(CreateSchemaOp)
def create_schema(operations, operation):
    operations.execute("CREATE SCHEMA %s" % operation.target.name)


@Operations.implementation_for(DropSchemaOp)
def drop_schema(operations, operation):
    operations.execute("DROP SCHEMA %s" % operation.target.name)


@Operations.implementation_for(CreateSPOp)
def create_sp(operations, operation):
    operations.execute(
        "CREATE FUNCTION %s %s" % (
            operation.target.name, operation.target.args[0]
        )
    )


@Operations.implementation_for(DropSPOp)
def drop_sp(operations, operation):
    operations.execute("DROP FUNCTION %s" % operation.target.name)


@Operations.implementation_for(CreateTriggerOp)
def create_trigger(operations, operation):
    args = operation.target.args
    operations.execute(
        "CREATE TRIGGER %s %s ON %s %s" % (
            operation.target.name, args[0], args[1], args[2]
        )
    )


@Operations.implementation_for(DropTriggerOp)
def drop_trigger(operations, operation):
    operations.execute(
        "DROP TRIGGER %s ON %s" % (
            operation.target.name,
            operation.target.args[1]
        )
    )


@Operations.implementation_for(CreatePolicyOp)
def create_policy(operations, operation):
    operations.execute(
        "CREATE POLICY %s ON %s %s" % (
            operation.target.name,
            operation.target.args[0],
            operation.target.args[1],
        )
    )


@Operations.implementation_for(DropPolicyOp)
def drop_policy(operations, operation):
    operations.execute(
        "DROP POLICY %s ON %s" % (
            operation.target.name,
            operation.target.args[0],
        )
    )
