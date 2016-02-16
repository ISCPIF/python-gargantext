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
    user_id = Column(Integer, ForeignKey(User.id))
    parent_id = Column(Integer, ForeignKey('nodes.id'))
    # main data
    name = Column(String(255))
    date  = Column(DateTime(), default=datetime.now)
    # metadata
    hyperdata = Column(JSONB, default={})

    def __getitem__(self, key):
        return self.hyperdata[key]

    def __setitem__(self, key, value):
        self.hyperdata[key] = value

    def children(self, typename=None):
        """Return a query to all the direct children of the current node.
        Allows filtering by typename (see `constants.py`)
        """
        query = session.query(Node).filter(Node.parent_id == self.id)
        if typename is not None:
            query = query.filter(Node.typename == typename)
        return query

    def add_child(self, typename, **kwargs):
        """Create and return a new direct child of the current node.
        """
        return Node(
            user_id = self.user_id,
            typename = typename,
            parent_id = self.id,
            **kwargs
        )

    def add_corpus(self, name, resource_type, resource_upload=None, resource_url=None):
        if resource_upload is not None:
            resource_path = upload(resource_upload)
        else:
            resource_path = None
        corpus = self.add_child('CORPUS', name=name, hyperdata={
            'resource_type': int(resource_type),
            'resource_path': resource_path,
            'resource_url': resource_url,
        })
        session.add(corpus)
        session.commit()
        return corpus
