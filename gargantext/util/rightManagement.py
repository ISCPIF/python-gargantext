from gargantext.util.db import *
#from gargantext.util.db_cache import cache
from gargantext.models import *


def set_rights_pure(nodeUser, user=None, group=None, others=None):
    """
    set_rights ::    NodeUser
                  -> Maybe (Int, Int)
                  -> Maybe (Int, Int)
                  -> Maybe Int
                  -> NodeUser

    """
    if user is not None:
        user_id, mode_user = user
        nodeUser.user_id   = user_id
        nodeUser.mode_user = mode_user

    if group is not None:
        group_id, mode_group = group
        nodeUser.group_id    = group_id
        nodeUser.mode_group  = mode_group

    if others is not None:
        nodeUser.mode_others = others

    return nodeUser


def set_rights(node_id, user_id=None, group_id=None, rights=(7,0,0)):
    """
    Set rights of a node
    """
    nodeUser = session.query(NodeUser).filter(NodeUser.node_id == node_id).first()

    if nodeUser is None:
        nodeUser = NodeUser()
        nodeUser


def share_node(node_id, user_id=None)

def share_corpus(corpus_id, user_id=None, )

def share_project()

def share_document()
