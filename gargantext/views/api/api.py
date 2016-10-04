from rest_framework.status      import *
from rest_framework.exceptions  import APIException
from rest_framework.response    import Response
from rest_framework.renderers   import JSONRenderer, BrowsableAPIRenderer
from rest_framework.views       import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from gargantext.constants       import RESOURCETYPES, NODETYPES, get_resource
from gargantext.models          import Node, Ngram, NodeNgram, NodeNodeNgram, NodeNode
from gargantext.util.db         import session, delete, func, bulk_insert
from gargantext.util.db_cache   import cache, or_
from gargantext.util.files      import upload
from gargantext.util.http       import ValidationException, APIView, JsonHttpResponse, get_parameters
from gargantext.util.scheduling import scheduled
from gargantext.util.validation import validate

#import

#NODES format
_user_default_fields =["is_staff","is_superuser","is_active",  "username", "email", "first_name", "last_name", "id"]
_api_default_fields = ['id', 'parent_id', 'name', 'typename', 'date']
_doc_default_fields = ['id', 'parent_id', 'name', 'typename', 'date', "hyperdata"]
#_resource_default_fields = [['id', 'parent_id', 'name', 'typename', "hyperdata.method"]
#_corpus_default_fields = ['id', 'parent_id', 'name', 'typename', 'date', "hyperdata","resource"]

def format_parent(node):
    '''format the parent'''
    try:
        #USER
        if node.username != "":
            return {field: getattr(node, field) for field in _user_default_fields}
    except:
        #DOC
        if node.typename == "DOCUMENT":
            return {field: getattr(node, field) for field in _doc_default_fields}

        elif node.typename == "CORPUS":
            parent = {field: getattr(node, field) for field in _doc_default_fields}
            #documents
            #parent["documents"] = {"count":node.children("DOCUMENT").count()}
            #resources
            #parent["resources"] = {"count":node.children("RESOURCE").count()}
            #status


                    #return {field: getattr(node, field) for field in _doc_default_fields}
            parent["status_msg"] = status_message
            return parent
        #PROJECT, RESOURCES?
        else:
            return {field: getattr(node, field) for field in _api_default_fields}

def format_records(node_list):
    '''format the records list'''
    if len(node_list) == 0:
        return []
    node1 = node_list[0]
    #USER
    if node1.typename == "USER":
        return [{field: getattr(node, field) for field in _user_default_fields} for node in node_list]
    #DOCUMENT
    elif node1.typename == "DOCUMENT":
        return [{field: getattr(node, field) for field in _doc_default_fields} for node in node_list]
    #CORPUS, PROJECT, RESOURCES?
    elif node1.typename == "CORPUS":

        records = []
        for node in node_list:
            #PROJECTS VIEW SHOULD NE BE SO DETAILED
            record = {field: getattr(node, field) for field in _doc_default_fields}
            record["resources"] = [n.id for n in node.children("RESOURCE")]
            record["documents"] = [n.id for n in node.children("DOCUMENT")]
            #record["resources"] = format_records([n for n in node.children("RESOURCE")])
            #record["documents"] = format_records([n for n in node.children("DOCUMENT")])
            status = node.status()
            if status is not None and not status['complete']:

                  if not status['error']:
                      status_message = '(in progress: %s, %d complete)' % (
                          status['action'].replace('_', ' '),
                          status['progress'],
                      )
                  else:
                      status_message = '(aborted: "%s" after %i docs)' % (
                          status['error'][-1],
                          status['progress']
                      )
            else:
                  status_message = ''
            record["status"] = status_message
            records.append(record)
        return records
    else:
        return [{field: getattr(node, field) for field in _api_default_fields} for node in node_list]


def check_rights(request, node_id):
    '''check that the node belong to USER'''
    node = session.query(Node).filter(Node.id == node_id).first()
    if node is None:
        raise APIException("403 Unauthorized")
        # return Response({'detail' : "Node #%s not found" %(node_id) },
        #                      status = status.HTTP_404_NOT_FOUND)


    elif node.user_id != request.user.id:
        #response_data = {"log": "Unauthorized"}
        #return JsonHttpResponse(response_data, status=403)
        raise APIException("403 Unauthorized")
    else:
        return node

def format_response(parent, records):
    #print(records)
    return {   "parent": format_parent(parent),
                "records": format_records(records),
                "count":len(records)
            }
