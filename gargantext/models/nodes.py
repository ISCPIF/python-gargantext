from gargantext.util.db import *
from gargantext.util.files import upload
from gargantext.constants import *

from datetime import datetime

from .users import User


__all__ = ['Node']


class NodeType(TypeDecorator):
    """Define a new type of column to describe a Node's type.
    This column type is implemented as an SQL integer.
    Values are detailed in `gargantext.constants.NODETYPES`.
    """
    impl = Integer
    def process_bind_param(self, typename, dialect):
        return NODETYPES.index(typename)
    def process_result_value(self, typeindex, dialect):
        return NODETYPES[typeindex]

class Node(Base):
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    typename = Column(NodeType, index=True)
    # foreign keys
    user_id = Column(Integer, ForeignKey(User.id, ondelete='CASCADE'))
    parent_id = Column(Integer, ForeignKey('nodes.id', ondelete='CASCADE'))
    # main data
    name = Column(String(255))
    date  = Column(DateTime(), default=datetime.now)
    # metadata (see https://bashelton.com/2014/03/updating-postgresql-json-fields-via-sqlalchemy/)
    hyperdata = Column(JSONB, default=dict)

    def __init__(self, **kwargs):
        if 'hyperdata' not in kwargs:
            kwargs['hyperdata'] = kwargs.get('hyperdata', {})
        Base.__init__(self, **kwargs)

    def __getitem__(self, key):
        return self.hyperdata[key]

    def __setitem__(self, key, value):
        self.hyperdata[key] = value

    def save_hyperdata(self):
        """This is a necessary, yet ugly trick.
        Indeed, PostgreSQL does not yet manage incremental updates (see
        https://bashelton.com/2014/03/updating-postgresql-json-fields-via-sqlalchemy/)
        """
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(self, 'hyperdata')
        # # previous trick (even super-uglier)
        # hyperdata = self.hyperdata
        # self.hyperdata = None
        # session.add(self)
        # session.commit()
        # self.hyperdata = hyperdata
        # session.add(self)
        # session.commit()

    def children(self, typename=None):
        """Return a query to all the direct children of the current node.
        Allows filtering by typename (see `constants.py`)
        """
        query = session.query(Node).filter(Node.parent_id == self.id)
        if typename is not None:
            query = query.filter(Node.typename == typename)
        return query

    def add_child(self, **kwargs):
        """Create and return a new direct child of the current node.
        """
        return Node(
            user_id = self.user_id,
            parent_id = self.id,
            **kwargs
        )

    def resources(self):
        if 'resources' not in self.hyperdata:
            self['resources'] = MutableList()
        return self['resources']

    def add_resource(self, type, path=None, url=None):
        self.resources().append(MutableDict(
            {'type': type, 'path':path, 'url':url, 'extracted': False}
        ))

    def status(self, action=None, progress=None):
        if 'status' not in self.hyperdata:
            self['status'] = MutableDict(
                {'action': action, 'progress': progress}
            )
        else:
            if action is not None:
                self['status']['action'] = action
            if progress is not None:
                self['status']['progress'] = progress
        return self['status']
