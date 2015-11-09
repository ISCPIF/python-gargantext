from django.shortcuts import redirect
from django.shortcuts import render
from django.db import transaction

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template.loader import get_template
from django.template import Context

from node import models
# from node.models import Node_Ngram
from django.db import connection
#from node.models import Language, ResourceType, Resource, \
#        Node, NodeType, Node_Resource, Project, Corpus, \
#        Ngram, Node_Ngram, NodeNgramNgram, NodeNodeNgram

from node.admin import CorpusForm, ProjectForm, ResourceForm, CustomForm

from django.contrib.auth.models import User

import datetime
from itertools import *
from dateutil.parser import parse

from django.db import connection
from django import forms


from collections import defaultdict

from parsing.FileParsers import *
import os
import json
import math

# SOME FUNCTIONS

from gargantext_web import settings

from django.http import *
from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from scrappers.scrap_pubmed.admin import Logger

from gargantext_web.db import *

from sqlalchemy import or_, func

from gargantext_web import about

from rest_v1_0.api import JsonHttpResponse


from ngram.lists import listIds, listNgramIds, ngramList , doList


def test_page(request , project_id , corpus_id):

    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = int(project_id)
        offset = int(corpus_id)
    except ValueError:
        raise Http404()

    t = get_template('tests/test_select-boostrap.html')

    user = cache.User[request.user.username].id
    date = datetime.datetime.now()
    project = cache.Node[int(project_id)]
    corpus  = cache.Node[int(corpus_id)]
    type_doc_id = cache.NodeType['Document'].id
    number = session.query(func.count(Node.id)).filter(Node.parent_id==corpus_id, Node.type_id==type_doc_id).all()[0][0]
    try:
        processing = corpus.hyperdata['Processing']
    except Exception as error:
        print(error)
        processing = 0

    html = t.render(Context({
            'debug': settings.DEBUG,
            'user': request.user.username,
            'date': date,
            'project': project,
            'corpus' : corpus,
            'processing' : processing,
            'number' : number,
            }))

    return HttpResponse(html)

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
    number = session.query(func.count(Node.id)).filter(Node.parent_id==corpus_id, Node.type_id==type_doc_id).all()[0][0]
    myamlist_type_id = cache.NodeType['MiamList'].id
    miamlist = session.query(Node).filter(Node.user_id == request.user.id , Node.parent_id==corpus_id , Node.type_id == myamlist_type_id ).first()

    try:
        processing = corpus.hyperdata['Processing']
    except Exception as error:
        print(error)
        processing = 0

    html = t.render(Context({
            'debug': settings.DEBUG,
            'user': request.user.username,
            'date': date,
            'project': project,
            'corpus' : corpus,
            'processing' : processing,
            'number' : number,
            'list_id': miamlist.id,
            }))

    return HttpResponse(html)


def get_stoplist(request , corpus_id , doc_id):
    """Get All for a doc id"""

    user_id = request.user.id
    whitelist_type_id = cache.NodeType['WhiteList'].id
    document_type_id = cache.NodeType['Document'].id
    miam_id = listIds(typeList='MiamList', user_id=request.user.id, corpus_id=corpus_id)[0][0]
    count_min = 2
    size = 1000

    corpus_id = int(corpus_id)
    lists = dict()
    for list_type in ['StopList']:
        list_id = list()
        list_id = listIds(user_id=request.user.id, corpus_id=int(corpus_id), typeList=list_type)
        lists["%s" % list_id[0][0]] = list_type
    doc_ngram_list = listNgramIds(corpus_id=corpus_id, list_id=list_id[0][0], doc_id=list_id[0][0], user_id=request.user.id)
    StopList = {}
    for n in doc_ngram_list:
        StopList[ n[0] ] = True

    results = StopList.keys() #[ "hola" , "mundo" ]
    return JsonHttpResponse(StopList)


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
    number = session.query(func.count(Node.id)).filter(Node.parent_id==corpus_id, Node.type_id==type_doc_id).all()[0][0]

    try:
        processing = corpus.hyperdata['Processing']
    except Exception as error:
        print(error)
        processing = 0

    html = t.render(Context({
            'debug': settings.DEBUG,
            'user': request.user.username,
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
    documents  = session.query(Node).filter(Node.user_id == user_id , Node.parent_id==corpus_id , Node.type_id == document_type_id ).all()
    for doc in documents:
        if "journal" in doc.hyperdata:
            journal = doc.hyperdata["journal"]
            if journal not in JournalsDict:
                JournalsDict [journal] = 0
            JournalsDict[journal] += 1
    return JsonHttpResponse(JournalsDict)

from gargantext_web.db import session, cache, Node, NodeNgram
from sqlalchemy import or_, func
from sqlalchemy.orm import aliased
def get_ngrams_json(request , project_id, corpus_id ):
    results = ["holaaaa" , "mundo"]

    user_id = request.user.id
    whitelist_type_id = cache.NodeType['WhiteList'].id
    document_type_id = cache.NodeType['Document'].id
    miam_id = listIds(typeList='MiamList', user_id=request.user.id, corpus_id=corpus_id)[0][0]
    count_min = 2
    size = 1000

    corpus_id = int(corpus_id)
    lists = dict()
    for list_type in ['StopList']:
        list_id = list()
        list_id = listIds(user_id=request.user.id, corpus_id=int(corpus_id), typeList=list_type)
        lists["%s" % list_id[0][0]] = list_type
    doc_ngram_list = listNgramIds(corpus_id=corpus_id, list_id=list_id[0][0], doc_id=list_id[0][0], user_id=request.user.id)
    StopList = {}
    for n in doc_ngram_list:
        StopList[ n[0] ] = True


    # [ Get Uniq_Occs ]
    myamlist_type_id = cache.NodeType['MiamList'].id
    myamlist = session.query(Node).filter(Node.user_id == user_id , Node.parent_id==corpus_id , Node.type_id == myamlist_type_id ).first()
    myamlists = session.query(Node).filter(Node.user_id == user_id , Node.parent_id==corpus_id , Node.type_id == myamlist_type_id ).all()
    # sql_average = """SELECT avg(weight) as Average FROM node_node_ngram WHERE node_node_ngram.node_id=%d""" % (myamlist.id)
    # cursor = connection.cursor()
    # cursor.execute(sql_average)
    # avg_result = cursor.fetchone()[0]
    # threshold = min (10 , math.sqrt(avg_result) )

    # OCCs  = session.query(Node_Ngram).filter( Node_Ngram.node_id==myamlist.id , Node_Ngram.weight >= threshold ).all()
    # [ / Get Uniq_Occs ]
    Miam = aliased(NodeNgram)
    sql_average = (session.query(NodeNgram.ngram_id, func.sum(NodeNgram.weight))
                          .join(Node, Node.id == NodeNgram.node_id)
                          .join(Miam, Miam.ngram_id == NodeNgram.ngram_id)
                          .filter(Node.parent_id == corpus_id, Node.type_id==cache.NodeType['Document'].id)
                          .filter(Miam.node_id==myamlist.id)
                          .group_by(NodeNgram.ngram_id)
                          .all()
                  )

    # print([n for n in sql_average])
    OCCs = {}
    for ngram in sql_average:
        OCCs [ ngram[0] ] = ngram[1]



    # [ Initializing Ngrams_Scores with occ_uniq ]
    Ngrams_Scores = {}

    for ngram in OCCs:
        if ngram not in StopList:
            if ngram not in Ngrams_Scores:
                Ngrams_Scores[ngram] = {}
                Ngrams_Scores[ngram]["scores"] = {
                        "occ_uniq": round(OCCs[ngram]),
                        "tfidf_sum": 0.0
                    }
    # [ / Initializing Ngrams_Scores with occ_uniq ]



    # [ Getting TF-IDF scores (sum per each ngram) ]
    NgramTFIDF = session.query(NodeNodeNgram).filter( NodeNodeNgram.nodex_id==corpus_id ).all()
    for ngram in NgramTFIDF:
        if ngram.ngram_id not in StopList:
            if ngram.ngram_id in Ngrams_Scores:
                Ngrams_Scores[ngram.ngram_id]["scores"]["tfidf_sum"] += ngram.score
    # [ / Getting TF-IDF scores ]



    # [ Preparing JSON-Array full of Scores! ]
    Metrics = {
        "ngrams":[],
        "scores": {}
    }

    ngrams_ids = Ngrams_Scores.keys()
    query = session.query(Ngram).filter(Ngram.id.in_( ngrams_ids ))
    ngrams_data = query.all()
    for ngram in ngrams_data:
        if ngram.id not in StopList:
            occ_uniq = occ_uniq = Ngrams_Scores[ngram.id]["scores"]["occ_uniq"]
            Ngrams_Scores[ngram.id]["name"] = ngram.terms
            Ngrams_Scores[ngram.id]["id"] = ngram.id
            Ngrams_Scores[ngram.id]["scores"]["tfidf"] = Ngrams_Scores[ngram.id]["scores"]["tfidf_sum"] / occ_uniq
            del Ngrams_Scores[ngram.id]["scores"]["tfidf_sum"]
            Metrics["ngrams"].append( Ngrams_Scores[ngram.id] )



    Metrics["scores"] = {
        "initial":"occ_uniq",
        "nb_docs":1,
        "orig_nb_ngrams":1,
        "nb_ngrams":len(Metrics["ngrams"]),
        # "occs_threshold":threshold
    }
    # [ / Preparing JSON-Array full of Scores! ]


    # print("miamlist:",myamlist.id)
    # print("sql avg:",sql_average)
    # print (avg_result)
    # print ("LALALALALALALALLLALALALALA")

    return JsonHttpResponse(Metrics)
