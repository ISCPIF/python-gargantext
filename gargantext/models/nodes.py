from gargantext.util.db import *
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
    type = Column(NodeType, index=True)
    user_id = Column(Integer, ForeignKey(User.id))
    # main data
    name = Column(String(255), unique=True)
    date  = Column(DateTime(), default=datetime.now)
    # metadata
    hyperdata = Column(JSONB, default={})
