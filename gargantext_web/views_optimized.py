
import os

from django.shortcuts import redirect
from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden

from sqlalchemy import func, and_, or_
from sqlalchemy.orm import aliased

from collections import defaultdict
from datetime import datetime
from time import sleep
from threading import Thread

from node.admin import CustomForm
from gargantext_web.db import *
from gargantext_web.db import get_or_create_node
from gargantext_web.views import session

from gargantext_web.settings import DEBUG, MEDIA_ROOT
from rest_v1_0.api import JsonHttpResponse
from django.db import connection

import json
import re

from parsing.corpustools import add_resource, parse_resources, extract_ngrams
from ngram.tfidf import compute_tfidf

from gargantext_web.celery import apply_workflow

from admin.utils import ensure_dir

def project(request, project_id):
    # do we have a valid project id?
    try:
        project_id = int(project_id)
    except ValueError:
        raise Http404()

    # do we have a valid project?

    project = (session
        .query(Node)
        .filter(Node.id == project_id)
        .filter(Node.type_id == cache.NodeType['Project'].id)
    ).first()
    if project is None:
        raise Http404()

    # do we have a valid user?
    user = request.user
    if not user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)
    if project.user_id != user.id:
        in_group = """ SELECT user_parent FROM node_user_user WHERE user_id=%d""" % ( int(user.id)  )
        cursor = connection.cursor()
        cursor.execute(in_group)
        in_group = False
        for c in cursor.fetchall():
            if c[0]==project.user_id:
                in_group = True
        if not in_group:
            return JsonHttpResponse( {"request" : "forbidden"} )

    # Let's find out about the children nodes of the project
    ChildrenNode = aliased(Node)
    # This query is giving you the wrong number of docs from the pubmedquerier (x 5)
    #  ... sqlalchemy.func by Resource.type_id is the guilty
    # ISSUE L51
    corpus_query = (session
        .query(Node.id, Node.name, func.count(ChildrenNode.id), Node.hyperdata['Processing'])
        #.query(Node.id, Node.name, Resource.type_id, func.count(ChildrenNode.id))
        #.join(Node_Resource, Node_Resource.node_id == Node.id)
        #.join(Resource, Resource.id == Node_Resource.resource_id)
        .filter(Node.parent_id == project.id)
        .filter(Node.type_id == cache.NodeType['Corpus'].id)
        .filter(and_(ChildrenNode.parent_id  == Node.id, ChildrenNode.type_id  == cache.NodeType['Document'].id))
        .group_by(Node.id, Node.name)
        .order_by(Node.name)
        .all()
    )
    corpora_by_resourcetype = defaultdict(list)
    documents_count_by_resourcetype = defaultdict(int)
    corpora_count = 0
    corpusID_dict = {}


    for corpus_id, corpus_name, document_count, processing in corpus_query:
        #print(corpus_id, processing)
        # Not optimized GOTO ISSUE L51
        try:
            resource_type_id = (session.query(Resource.type_id)
                                       .join(Node_Resource, Node_Resource.resource_id == Resource.id)
                                       .join(Node, Node.id == Node_Resource.node_id )
                                       .filter(Node.id==corpus_id)
                                       .first())[0]
        except:
            pass

        if not corpus_id in corpusID_dict:
            if resource_type_id is None:
                resourcetype_name = '(no resource)'
            else:
                resourcetype = cache.ResourceType[resource_type_id]
                resourcetype_name = resourcetype.name
            corpora_by_resourcetype[resourcetype_name].append({
                'id'        : corpus_id,
                'name'      : corpus_name,
                'count'     : document_count,
                'processing': processing,
            })
            documents_count_by_resourcetype[resourcetype_name] += document_count
            corpora_count += 1
            corpusID_dict[corpus_id]=True

    # do the donut
    total_documents_count = sum(documents_count_by_resourcetype.values())
    donut = [
        {   'source': re.sub(' \(.*$', '', key),
            'count': value,
            'part' : round(value * 100 / total_documents_count) if total_documents_count else 0,
        }
        for key, value in documents_count_by_resourcetype.items()
    ]

    # deal with the form
    if request.method == 'POST':
        # form validation
        form = CustomForm(request.POST, request.FILES)
        if form.is_valid():

            # extract information from the form
            name = form.cleaned_data['name']
            thefile = form.cleaned_data['file']
            resourcetype = cache.ResourceType[form.cleaned_data['type']]

            # corpus node instanciation as a Django model
            corpus = Node(
                name        = name,
                user_id     = request.user.id,
                parent_id   = project_id,
                type_id     = cache.NodeType['Corpus'].id,
                # no default language at this point
                language_id = None,
                hyperdata    = {'Processing' : "Parsing documents",}
            )
            session.add(corpus)
            session.commit()

            # If user is new, folder does not exist yet, create it then
            ensure_dir(request.user)

            # Save the uploaded file
            filepath = '%s/corpora/%s/%s' % (MEDIA_ROOT, request.user.username, thefile._name)
            f = open(filepath, 'wb')
            f.write(thefile.read())
            f.close()
            # add the uploaded resource to the corpus
            add_resource(corpus,
                user_id = request.user.id,
                type_id = resourcetype.id,
                file = filepath,
            )
            # let's start the workflow
            try:
                if DEBUG is False:
                    apply_workflow.apply_async((corpus.id,),)
                else:
                   #apply_workflow(corpus)
                   thread = Thread(target=apply_workflow, args=(corpus.id, ), daemon=True)
                   thread.start()
            except Exception as error:
                print('WORKFLOW ERROR')
                print(error)
            # redirect to the main project page
            # TODO need to wait before response (need corpus update)
            sleep(2)
            return HttpResponseRedirect('/project/' + str(project_id))
        else:
            print('ERROR: BAD FORM')
    else:
        form = CustomForm()


    # HTML output
    return render(request, 'project.html', {
        'form'          : form,
        'user'          : user,
        'date'          : datetime.now(),
        'project'       : project,
        'donut'         : donut,
        'list_corpora'  : dict(corpora_by_resourcetype),
        'whitelists'    : '',
        'blacklists'    : '',
        'cooclists'     : '',
        'number'        : corpora_count,
    })

def tfidf(request, corpus_id, ngram_ids):
    """Takes IDs of corpus and ngram and returns list of relevent documents in json format
    according to TFIDF score (order is decreasing).
    """
    limit=5
    nodes_list = []
    # filter input
    ngram_ids = ngram_ids.split('a')
    ngram_ids = [int(i) for i in ngram_ids]
    
    corpus = session.query(Node).filter(Node.id==corpus_id).first()
    
    tfidf_id = get_or_create_node(corpus=corpus, nodetype='Tfidf').id
    print(tfidf_id)
    # request data
    nodes_query = (session
        .query(Node, func.sum(NodeNodeNgram.score))
        .join(NodeNodeNgram, NodeNodeNgram.nodey_id == Node.id)
        .filter(NodeNodeNgram.nodex_id == tfidf_id)
        .filter(Node.type_id == cache.NodeType['Document'].id)
        .filter(or_(*[NodeNodeNgram.ngram_id==ngram_id for ngram_id in ngram_ids]))
        .group_by(Node)
        .order_by(func.sum(NodeNodeNgram.score).desc())
        .limit(limit)
    )
    # print("\n")
    # print("in TFIDF:")
    # print("\tcorpus_id:",corpus_id)
    # convert query result to a list of dicts
    if nodes_query is None:
        print("TFIDF error, juste take sums")
        nodes_query = (session
            .query(Node, func.sum(NodeNgram.weight))
            .join(NodeNgram, NodeNgram.node_id == Node.id)
            .filter(Node.parent_id == corpus_id)
            .filter(Node.type_id == cache.NodeType['Document'].id)
            .filter(or_(*[NodeNgram.ngram_id==ngram_id for ngram_id in ngram_ids]))
            .group_by(Node)
            .order_by(func.sum(NodeNgram.weight).desc())
            .limit(limit)
        )

    for node, score in nodes_query:
        print("\t corpus:",corpus_id,"\t",node.name)
        node_dict = {
            'id': node.id,
            'score': score,
        }
        for key in ('title', 'publication_date', 'journal', 'authors', 'fields'):
            if key in node.hyperdata:
                node_dict[key] = node.hyperdata[key]
        nodes_list.append(node_dict)

    return JsonHttpResponse(nodes_list)

def getCorpusIntersection(request , corpuses_ids):
    FinalDict = False
    if request.method == 'POST' and "nodeids" in request.POST and len(request.POST["nodeids"])>0 :

        import ast
        import networkx as nx
        node_ids = [int(i) for i in (ast.literal_eval( request.POST["nodeids"] )) ]
        # Here are the visible nodes of the initial semantic map.

        corpuses_ids = corpuses_ids.split('a')
        
        corpuses_ids = [int(i) for i in corpuses_ids] 
        print(corpuses_ids)
        # corpus[1] will be the corpus to compare
        
        

        def get_score(corpus_id):

            cooc_type_id = cache.NodeType['Cooccurrence'].id
            cooc_ids  = (session.query(Node.id)
                                .filter(Node.user_id == request.user.id
                                      , Node.parent_id==corpus_id
                                      , Node.type_id == cooc_type_id )
                                .first()
                                )
            
            if len(cooc_ids)==0:
                return JsonHttpResponse(FinalDict)
                # If corpus[1] has a coocurrence.id then lets continue

            Coocs  = {}
            
            G = nx.Graph()
            # undirected graph only
            # because direction doesnt matter here
            # coocs is triangular matrix

            ngrams_data = ( session.query(NodeNgramNgram)
                                   .filter( NodeNgramNgram.node_id==cooc_ids[0]
                                          , or_(
                                                NodeNgramNgram.ngramx_id.in_( node_ids )
                                              , NodeNgramNgram.ngramy_id.in_( node_ids )
                                              )
                                              )
                                   .group_by(NodeNgramNgram)
                                   .all()
                                   )
            
            for ngram in ngrams_data :
                # are there visible nodes in the X-axis of corpus to compare ?
                G.add_edge(  ngram.ngramx_id ,  ngram.ngramy_id , weight=ngram.score)
                print(corpus_id, ngram)

            for e in G.edges_iter() :
                n1 = e[0]
                n2 = e[1]
                # print( G[n1][n2]["weight"] , "\t", n1,",",n2 )
                if n1 not in Coocs :
                    Coocs[n1] = 0
                if n2 not in Coocs :
                    Coocs[n2] = 0
                Coocs[n1] += G[n1][n2]["weight"]
                Coocs[n2] += G[n1][n2]["weight"]

            return(Coocs,G)

        Coocs_0,G_0 = get_score( corpuses_ids[0] )
        Coocs_1,G_1 = get_score( corpuses_ids[1] )
        
        FinalDict = {}
        measure = 'cooc'
        
        if measure == 'jacquard':
            for node in node_ids :
                if node in G_1.nodes() and node in G_0.nodes():
                    neighbors_0 = set(G_0.neighbors(node))
                    neighbors_1 = set(G_1.neighbors(node))
                    jacquard = len(neighbors_0.intersection(neighbors_1)) / len(neighbors_0.union(neighbors_1))
                    FinalDict[node] = jacquard * 3
                elif node in G_0.nodes() and node not in G_1.nodes() :
                    FinalDict[node] = 2
                elif node not in G_0.nodes() and node in G_1.nodes() :
                    FinalDict[node] = 1
                else:
                    FinalDict[node] = 0
        
        elif measure == 'cooc':
            for node in node_ids :
                if node in G_1.nodes() and node in G_0.nodes():
                    score_0 = Coocs_0[node] / G_0.degree(node)
                    score_1 = Coocs_1[node] / G_1.degree(node)
                    FinalDict[node] = 5 * score_0 / score_1
                elif node in G_0.nodes() and node not in G_1.nodes() :
                    FinalDict[node] = 0.5
                elif node not in G_0.nodes() and node in G_1.nodes() :
                    FinalDict[node] = 0.2
                else:
                    FinalDict[node] = 0
        
        print(FinalDict)
                #print(node,score)
                # Getting AVG-COOC of each ngram that exists in the cooc-matrix of the compared-corpus. 

    return JsonHttpResponse(FinalDict)

def getUserPortfolio(request , project_id):
    user = request.user
    user_id         = cache.User[request.user.username].id
    project_type_id = cache.NodeType['Project'].id
    corpus_type_id = cache.NodeType['Corpus'].id

    results = {}
    projs = session.query(Node).filter(Node.user_id == user_id,Node.type_id==project_type_id ).all()


    in_group = """ SELECT user_parent FROM node_user_user WHERE user_id=%d""" % ( int(user_id)  )
    cursor = connection.cursor()
    cursor.execute(in_group)
    for c in cursor.fetchall():
        user_parent = c[0]
        more_projs = session.query(Node).filter(Node.user_id == user_parent,Node.type_id==project_type_id ).all()
        if more_projs!=None:
            for p in more_projs:
                projs.append( p )

    for i in projs:
        # print (i.id,i.name)
        if i.id not in results: 
            results[i.id] = {}
        results[i.id]["proj_name"] = i.name
        results[i.id]["corpuses"] = []
        corpuses = session.query(Node).filter(Node.parent_id==i.id , Node.type_id==corpus_type_id).all()
        for j in corpuses:
            doc_count = session.query(func.count(Node.id)).filter(Node.parent_id==j.id).all()[0][0]
            if doc_count >= 10:
                # print(session.query(Node).filter(Node.id==j.id).first())
                info = { 
                    "id":j.id , 
                    "name":j.name ,
                    "c":doc_count
                }
                results[i.id]["corpuses"].append(info)
                # print("\t\t",j.id , j.name , doc_count)

        if len(results[i.id]["corpuses"])==0:
            del results[i.id]


    return JsonHttpResponse( results )
