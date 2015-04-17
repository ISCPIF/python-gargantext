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
from gargantext_web.settings import DEBUG, MEDIA_ROOT
from gargantext_web.api import JsonHttpResponse
import json
import re

from parsing.corpustools import add_resource, parse_resources, extract_ngrams, compute_tfidf


from gargantext_web.celery import apply_workflow

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
        return HttpResponseForbidden()

    # Let's find out about the children nodes of the project
    ChildrenNode = aliased(Node)
    # This query is giving you the wrong number of docs from the pubmedquerier (x 5)
    #  ... sqlalchemy.func by Resource.type_id is the guilty
    # ISSUE L51
    corpus_query = (session
        .query(Node.id, Node.name, func.count(ChildrenNode.id), Node.metadata['Processing'])
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
        resource_type_id = (session.query(Resource.type_id)
                                   .join(Node_Resource, Node_Resource.resource_id == Resource.id)
                                   .join(Node, Node.id == Node_Resource.node_id )
                                   .filter(Node.id==corpus_id)
                                   .first())[0]
        
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
            
            # which default language shall be used?
            if resourcetype.name == "Europress (French)":
                language_id = cache.Language['fr'].id
            elif resourcetype.name == "Europress (English)":
                language_id = cache.Language['en'].id
            else:
                language_id = None
            
            # corpus node instanciation as a Django model
            corpus = Node(
                name        = name,
                user_id     = request.user.id,
                parent_id   = project_id,
                type_id     = cache.NodeType['Corpus'].id,
                language_id = language_id,
                metadata    = {'Processing' : 1,}
            )
            session.add(corpus)
            session.commit()
            # save the uploaded file
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
            sleep(1)
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
    limit=6
    nodes_list = []
    # filter input
    ngram_ids = ngram_ids.split('a')
    ngram_ids = [int(i) for i in ngram_ids]
    # request data
    nodes_query = (session
        .query(Node, func.sum(NodeNodeNgram.score))
        .join(NodeNodeNgram, NodeNodeNgram.nodey_id == Node.id)
        .filter(NodeNodeNgram.nodex_id == corpus_id)
        .filter(NodeNodeNgram.ngram_id.in_(ngram_ids))
        .group_by(Node)
        .order_by(func.sum(NodeNodeNgram.score).desc())
        .limit(limit)
    )
    # print("\n")
    # print("in TFIDF:")
    # print("\tcorpus_id:",corpus_id)
    # convert query result to a list of dicts
    for node, score in nodes_query:
        print("\t corpus:",corpus_id,"\t",node.name)
        node_dict = {
            'id': node.id,
            'score': score,
        }
        for key in ('title', 'publication_date', 'journal', 'authors', 'fields'):
            if key in node.metadata:
                node_dict[key] = node.metadata[key]
        nodes_list.append(node_dict)

    # print("= = = = = = = = \n")
    data = json.dumps(nodes_list) 
    return JsonHttpResponse(data)
