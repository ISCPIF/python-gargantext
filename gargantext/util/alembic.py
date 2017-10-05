"""Define ReplaceableObject and related operations

Implements operations to create/drop SQL objects such as views, stored
procedures and triggers that can't be "altered" but can be replaced -- hence
the name of "ReplaceableObject" class.

This recipe is directly borrowed from Alembic documentation, see
http://alembic.zzzcomputing.com/en/latest/cookbook.html#replaceable-objects

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


@Operations.register_operation("create_view", "invoke_for_target")
@Operations.register_operation("replace_view", "replace")
class CreateViewOp(ReversibleOp):
    def reverse(self):
        return DropViewOp(self.target)


@Operations.register_operation("drop_view", "invoke_for_target")
class DropViewOp(ReversibleOp):
    def reverse(self):
        return CreateViewOp(self.target)


@Operations.register_operation("create_sp", "invoke_for_target")
@Operations.register_operation("replace_sp", "replace")
class CreateSPOp(ReversibleOp):
    def reverse(self):
        return DropSPOp(self.target)


@Operations.register_operation("drop_sp", "invoke_for_target")
class DropSPOp(ReversibleOp):
    def reverse(self):
        return CreateSPOp(self.target)


@Operations.register_operation("create_trigger", "invoke_for_target")
@Operations.register_operation("replace_trigger", "replace")
class CreateTriggerOp(ReversibleOp):
    def reverse(self):
        return DropTriggerOp(self.target)


@Operations.register_operation("drop_trigger", "invoke_for_target")
class DropTriggerOp(ReversibleOp):
    def reverse(self):
        return CreateTriggerOp(self.target)


@Operations.register_operation("create_role", "invoke_for_target")
@Operations.register_operation("replace_sp", "replace")
class CreateRoleOp(ReversibleOp):
    def reverse(self):
        return DropRoleOp(self.target)


@Operations.register_operation("drop_role", "invoke_for_target")
class DropRoleOp(ReversibleOp):
    def reverse(self):
        return CreateRoleOp(self.target)


@Operations.implementation_for(CreateViewOp)
def create_view(operations, operation):
    operations.execute("CREATE VIEW %s AS %s" % (
        operation.target.name,
        operation.target.args[0]
    ))


@Operations.implementation_for(DropViewOp)
def drop_view(operations, operation):
    operations.execute("DROP VIEW %s" % operation.target.name)


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
