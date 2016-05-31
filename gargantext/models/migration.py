from gargantext.util.db import *
from gargantext.util.files import upload
from gargantext.constants import *

from datetime import datetime

from .users import User


#__all__ = ['Node', 'NodeType', 'Language']

class NodeType_v2(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__  = 'node_nodetype'
    id             = Column(Integer, primary_key=True)
    name           = Column(String(255))

class Language_v2(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__  = 'node_language'
    id             = Column(Integer, primary_key=True)
    iso2           = Column(String(2))
    iso3           = Column(String(3))
    fullname       = Column(String(255))
    implemented    = Column(Boolean)


class Node_v2(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__  = 'node_node'
    id             = Column(Integer, primary_key=True)
    parent_id      = Column(Integer, ForeignKey('node_node.id'))
    user_id        = Column(Integer, ForeignKey(User.id))
    type_id        = Column(ForeignKey(NodeType_v2.id))
    name           = Column(String(255))
    language_id    = Column(Integer, ForeignKey(Language_v2.id))
    date           = Column(DateTime(), default=datetime.now)
    hyperdata      = Column(JSONB, default=dict)


def nodes_list(user_id, nodetype, parent_id=None, count=False):
    """
    nodes_list :: Int -> String -> Maybe Int -> Maybe Bool -> [(Int, String)]
    """
    nodes = ( session.query(Node_v2.id, Node_v2.name)
                     .join(NodeType_v2, NodeType_v2.id == Node_v2.type_id)
                     .filter(NodeType_v2.name == nodetype)
               )
    if parent_id is not None:
        nodes = nodes.filter(Node_v2.parent_id == parent_id)

    if count is True:
        return nodes.count()
    else:
        return nodes.all()

def nodes_tree(user_id):
    """
    nodes_tree :: Int -> Tree Nodes
    """
    for project_id, project_name in nodes_list(user_id, 'Project'):
        print("* Project (%d, %s)" % (project_id, project_name))
        for corpus_id, corpus_name in nodes_list(user_id, 'Corpus', parent_id=project_id):

            count =  nodes_list( user_id
                               , 'Document'
                               , parent_id=corpus_id
                               , count=True
                               )

            if count > 1:
                print("|- %d %s" % ( corpus_id, corpus_name ))
                print("  |- %s docs" % count)


