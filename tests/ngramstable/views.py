from django.shortcuts import redirect
# from django.shortcuts import render
# from django.db import transaction
# 
from django.http import Http404, HttpResponse #, HttpResponseRedirect, HttpResponseForbidden
from django.template.loader import get_template
from django.template import Context

from node import models
# from node.models import Node_Ngram
from django.db import connection
#from node.models import Language, ResourceType, Resource, \
#        Node, NodeType, Node_Resource, Project, Corpus, \
#        Ngram, Node_Ngram, NodeNgramNgram, NodeNodeNgram

# from node.admin import CorpusForm, ProjectForm, ResourceForm, CustomForm
# 
# from django.contrib.auth.models import User
# 
import datetime
# from itertools import *
# from dateutil.parser import parse
# 
# from django.db import connection
# from django import forms
# 
# 
# from collections import defaultdict
# 
# from parsing.FileParsers import *
# import os
import json
# import math

# SOME FUNCTIONS

from gargantext_web import settings
# 
# from django.http import *
# from django.shortcuts import render_to_response,redirect
# from django.template import RequestContext

# from gargantext_web.db import *

from gargantext_web.db import get_session, cache, Node, NodeNgram
from sqlalchemy import func

from rest_v1_0.api import JsonHttpResponse


def get_ngrams(request , project_id , corpus_id ):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = int(project_id)
        offset = int(corpus_id)
    except ValueError:
        raise Http404()

    t = get_template('corpus/terms.html')

    user = cache.User[request.user.username].id
    date = datetime.datetime.now()
    project = cache.Node[int(project_id)]
    corpus  = cache.Node[int(corpus_id)]
    type_doc_id = cache.NodeType['Document'].id

    session = get_session()
    number = session.query(func.count(Node.id)).filter(Node.parent_id==corpus_id, Node.type_id==type_doc_id).all()[0][0]
    myamlist_type_id = cache.NodeType['MiamList'].id
    miamlist = session.query(Node).filter(Node.parent_id==corpus_id , Node.type_id == myamlist_type_id ).first()

    the_query = """ SELECT hyperdata FROM node_node WHERE id=%d """ % ( int(corpus_id) )
    cursor = connection.cursor()
    try:
        cursor.execute(the_query)
        processing = cursor.fetchone()[0]["Processing"]
    except:
        processing = "Error"

    # [ how many groups ? ] #
    nb_groups = 0
    the_query = """ SELECT user_parent FROM node_user_user WHERE user_id=%d""" % ( int(request.user.id) )
    cursor = connection.cursor()
    try:
        cursor.execute(the_query)
        results = cursor.fetchall()
        nb_groups = len(results)
    except:
        pass
    # [ / how many groups ? ] #

    html = t.render(Context({
            'debug': settings.DEBUG,
            'user': request.user,
            'date': date,
            'project': project,
            'corpus' : corpus,
            'processing' : processing,
            'number' : number,
            'nb_groups' : nb_groups,
            'list_id': miamlist.id,
            }))

    return HttpResponse(html)

def get_journals(request , project_id , corpus_id ):

    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = int(project_id)
        offset = int(corpus_id)
    except ValueError:
        raise Http404()

    t = get_template('corpus/journals.html')

    user = cache.User[request.user.username].id
    date = datetime.datetime.now()
    project = cache.Node[int(project_id)]
    corpus  = cache.Node[int(corpus_id)]
    type_doc_id = cache.NodeType['Document'].id
    
    session = get_session()
    number = session.query(func.count(Node.id)).filter(Node.parent_id==corpus_id, Node.type_id==type_doc_id).all()[0][0]

    the_query = """ SELECT hyperdata FROM node_node WHERE id=%d """ % ( int(corpus_id) )
    cursor = connection.cursor()
    try:
        cursor.execute(the_query)
        processing = cursor.fetchone()[0]["Processing"]
    except:
        processing = "Error"

    html = t.render(Context({
            'debug': settings.DEBUG,
            'user': request.user,
            'date': date,
            'project': project,
            'corpus' : corpus,
            'processing' : processing,
            'number' : number,
            }))

    return HttpResponse(html)

def get_journals_json(request , project_id, corpus_id ):
    results = ["hola" , "mundo"]

    JournalsDict = {}

    user_id = request.user.id
    document_type_id = cache.NodeType['Document'].id
    
    session = get_session()
    documents  = session.query(Node).filter( Node.parent_id==corpus_id , Node.type_id == document_type_id ).all()
    
    for doc in documents:
        if "journal" in doc.hyperdata:
            journal = doc.hyperdata["journal"]
            if journal not in JournalsDict:
                JournalsDict [journal] = 0
            JournalsDict[journal] += 1
    return JsonHttpResponse(JournalsDict)




def get_corpuses( request , node_ids ):
    ngrams = [int(i) for i in node_ids.split("+") ]
    
    session = get_session()
    results = session.query(Node.id,Node.hyperdata).filter(Node.id.in_(ngrams) ).all()
    for r in results:
        print(r)
    return JsonHttpResponse( [ "tudo" , "bem" ] )


def get_cores( request ):
	import multiprocessing
	cpus = multiprocessing.cpu_count()
	return JsonHttpResponse( {"data":cpus} )


def get_corpus_state( request , corpus_id ):
    if not request.user.is_authenticated():
        return JsonHttpResponse( {"request" : "forbidden"} )
    processing = ["Waiting"]
    the_query = """ SELECT hyperdata FROM node_node WHERE id=%d """ % ( int(corpus_id) )
    cursor = connection.cursor()
    try:
        cursor.execute(the_query)
        processing = cursor.fetchone()[0]
    finally:
        connection.close()
    # processing = corpus.hyperdata['Processing']
    return JsonHttpResponse(  processing )


def get_groups( request ):
    """
    User groups for current user.id
    
    route: /get_groups
    """
    if not request.user.is_authenticated():
        return JsonHttpResponse( {"request" : "forbidden"} )

    # [ getting shared projects ] #
    common_users = []
    common_projects = []
    the_query = """ SELECT node_user_user.user_parent, auth_user.username \
                    FROM node_user_user, auth_user \
                    WHERE node_user_user.user_id=%d \
                    AND node_user_user.user_parent=auth_user.id """ % ( int(request.user.id) )
    cursor = connection.cursor()
    try:
        cursor.execute(the_query)
        common_users = cursor.fetchall()
    except:
        pass
    # [ / getting shared projects ] #

    return JsonHttpResponse(  common_users )


def graph_share(request, generic=100, specific=100):

    if request.method== 'GET' and "token" in request.GET:
        # import json
        le_token = json.loads(request.GET["token"])[0]
        import base64
        le_query = base64.b64decode(le_token).decode("utf-8")
        le_query = le_query.split("/")
        if len(le_query)<2: return JsonHttpResponse( {"request" : "forbidden"} )
        user_id = le_query[0]
        corpus_id = le_query[1]
        # resource_id = cache.ResourceType["Pubmed (xml format)"].id
        # corpus = session.query(Node).filter( Node.type_id==resource_id , Node.user_id==user_id , Node.id==corpus_id , Node.type_id == cache.NodeType['Corpus'].id ).first()
        # if corpus==None: return JsonHttpResponse( {"request" : "forbidden"} )
        
        session = get_session()
        miamlist = session.query(Node).filter( Node.user_id==user_id , Node.parent_id==corpus_id , Node.type_id == cache.NodeType['MiamList'].id ).first()
        
        if miamlist==None: return JsonHttpResponse( {"request" : "forbidden"} )
        graphurl = "node_link_share.json?token="+request.GET["token"]
        date = datetime.datetime.now()
        t = get_template('explorer_share.html')
        
        html = t.render(Context({\
                'debug': settings.DEBUG,
                'date'      : date,\
                'list_id'    : miamlist.id,\
                'graphfile' : graphurl,\
                }))
        return HttpResponse(html)

    return JsonHttpResponse(request.GET["token"])


def node_link_share(request):
    data = { "request" : "error" }
    if request.method== 'GET' and "token" in request.GET:
        # import json
        le_token = json.loads(request.GET["token"])[0]
        import base64
        le_query = base64.b64decode(le_token).decode("utf-8")
        le_query = le_query.split("/")
        if len(le_query)<2:
            return JsonHttpResponse( {"request" : "forbidden"} )
        user_id = le_query[0]
        corpus_id = le_query[1]

        from analysis.functions import get_cooc
        data = []
        
        session = get_session()
        corpus = session.query(Node).filter( Node.user_id==user_id , Node.id==corpus_id).first()
        data = get_cooc(request=request, corpus=corpus, type="node_link")

    return JsonHttpResponse(data)

def copy_corpus_GET(request , project_id , corpus_id):
    from node import copy
    corpus_id = int(corpus_id)
    user_id    = request.user.id
    project_id = project_id
    import random
    title = "clone_"+str(random.random())
    corpus_clone_id = copy.create_corpus(title, project_id=project_id, user_id=user_id)
    # print(corpus_clone_id)
    copy.copy_corpus(from_id=corpus_id, to_id=corpus_clone_id, title=title)
    return JsonHttpResponse([title , corpus_clone_id])

def share_resource(request , resource_id , group_id) :
    results = ["OK"]
    if request.method == 'POST':
        project2share = session.query(Node).filter(Node.user_id == request.user.id, Node.id == resource_id).first()
        if project2share!=None: # project exists?

            # [  is the received group in fact the group of the current user?  ]
            in_group = """ SELECT * FROM node_user_user WHERE user_id=%d AND user_parent=%d""" % ( int(request.user.id) , int(group_id) )
            cursor = connection.cursor()
            cursor.execute(in_group)
            if len(cursor.fetchall())<1:
                return JsonHttpResponse( {"request" : "forbidden"} )
            # [ / is the received group in fact the group of the current user?  ]

            # [  getting all childs ids of this project  ]
            ids2changeowner = [ project2share.id ]
            
            session = get_session()
            corpuses = session.query(Node.id).filter(Node.user_id == request.user.id, Node.parent_id==resource_id , Node.type_id == cache.NodeType["Corpus"].id ).all()
            
            for corpus in corpuses:
                ids2changeowner.append(corpus.id)
                lists = session.query(Node.id,Node.name).filter(Node.user_id == request.user.id, Node.parent_id==corpus.id ).all()
                for l in lists:
                    ids2changeowner.append(l.id)
            # [  / getting all childs ids of this project  ]

            # [  changing owner  ]
            print( "ids to change owner: ",len(ids2changeowner))
            print("old owner:", request.user.id , " | new owner:" , group_id)
            query = """UPDATE node_node set user_id=%d WHERE id IN (%s)""" % ( int(group_id) , ','.join((str(n) for n in ids2changeowner)) )
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                cursor.execute("COMMIT;")
            except Exception as error:
                print(error)
                pass
            connection.close()
            # [  / changing owner  ]

    return JsonHttpResponse(  results )
