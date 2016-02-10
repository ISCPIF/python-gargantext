from gargantext.util.db import *

from datetime import datetime

from .users import User


__all__ = ['NodeType', 'Node']


class NodeType(Base):
    __tablename__ = 'nodetypes'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)

class Node(Base):
    __tablename__ = 'nodes'
    id = Column(Integer, primary_key=True)
    # foreign keys
    user_id = Column(Integer, ForeignKey(User.id))
    type_id = Column(Integer, ForeignKey(NodeType.id))
    # main data
    name = Column(String(255), unique=True)
    date  = Column(DateTime(), default=datetime.now)
    # metadata
    hyperdata = Column(JSONB, default={})
