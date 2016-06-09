from gargantext.util.db import *
from gargantext.util.files import upload
from gargantext.constants import *
from gargantext.util.toolchain.main import parse_extract_indexhyperdata

from datetime import datetime

from .users import User
from .nodes import Node

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


class ResourceType(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__  = 'node_resourcetype'
    id             = Column(Integer, primary_key=True)
    name           = Column(String(255))

class NodeResource(Base):
    __table_args__ = {'extend_existing': True}
    __tablename__  = 'node_node_resource'
    id             = Column(Integer, primary_key=True)
    node_id        = Column(ForeignKey(Node_v2.id))
    resource_id    = Column(ForeignKey(ResourceType.id))
    parsed         = Column(Boolean)



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
                print("|__ %d %s" % ( corpus_id, corpus_name ))
                print("   |___ %s docs" % count)


def copy_nodes(node_id, to_parent_id=None, enabled=['PROJECT', 'CORPUS', 'DOCUMENT']):
    node = session.query(Node_v2).filter(Node_v2.id==node_id).first()
    
    nodetype = session.query(NodeType_v2).filter(NodeType_v2.id == node.type_id).first()
    
    resource = (session.query(ResourceType)
                           .join(NodeResource, NodeResource.resource_id == ResourceType.id)
                           .filter(NodeResource.node_id == node.id)
                           .first()
                           )
    
    nodetype_proj_id = session.query(NodeType_v2.id).filter(NodeType_v2.name == 'Project' ).first()
    nodetype_corp_id = session.query(NodeType_v2.id).filter(NodeType_v2.name == 'Corpus'  ).first()
    nodetype_docu_id = session.query(NodeType_v2.id).filter(NodeType_v2.name == 'Document').first()

    typename = nodetype.name.upper()

# Import a project:
#         new_project = Node(
#             user_id = user.id,
#             typename = 'PROJECT',
#             name = name,
#         )
#         session.add(new_project)
#         session.commit()

    if typename in enabled:
        parent_node = session.query(Node).filter(Node.id==to_parent_id).first()
        if parent_node is not None:
            corpus = parent_node.add_child(
                name = node.name,
                typename = typename
                )
            
            corpus.hyperdata['languages'] = {'fr' : 100}
            try:
                corpus.add_resource(
                    type = resourcetype(resource.name)
                    )
            except:
                corpus.add_resource(
                    type = resourcetype('Europress (French)')
                    )
            session.add(corpus)
            session.commit()
            print("%s copied" % corpus.name)


            nodes = (session.query(Node_v2)
                             .filter(Node_v2.parent_id == node.id)
                             .filter(Node_v2.type_id == nodetype_docu_id)
                    .all()
                    )

            for n in nodes:
                print(n.name)
                doc = corpus.add_child( name      = n.name
                                      , typename  = "DOCUMENT"
                                      , hyperdata = n.hyperdata
                                      )
                session.add(doc)
                session.commit()
            

#        else:
#            print("%d is None" % parent_id)

    else:
        print('%s is not enabled' % typename)




