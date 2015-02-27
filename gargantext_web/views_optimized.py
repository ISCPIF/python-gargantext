from django.shortcuts import redirect
from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseRedirect

from sqlalchemy import func
from sqlalchemy.orm import aliased

from collections import defaultdict
from datetime import datetime

from node.admin import CustomForm
from gargantext_web.db import *
from gargantext_web.settings import DEBUG

from parsing.corpus import parse_resources


def project(request, project_id):

    # SQLAlchemy session
    session = Session()

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
    corpus_query = (session
        .query(Node, Resource, func.count(ChildrenNode.id))
        .outerjoin(ChildrenNode, ChildrenNode.parent_id == Node.id)
        .join(Node_Resource, Node_Resource.node_id == Node.id)
        .join(Resource, Resource.id == Node_Resource.resource_id)
        .filter(Node.parent_id == project.id)
        .group_by(Node, Resource)
        .order_by(Node.name)
    )
    corpora_by_resourcetype = defaultdict(list)
    documents_count_by_resourcetype = defaultdict(int)
    corpora_count = 0
    for corpus, resource, document_count in corpus_query:
        resourcetype = cache.ResourceType[resource.type_id]
        resourcetype_name = resourcetype.name
        corpora_by_resourcetype[resourcetype_name].append({
            'id': corpus.id,
            'name': corpus.name,
            'count': document_count,
        })
        documents_count_by_resourcetype[resourcetype_name] += document_count
        corpora_count += 1

    # do the donut
    total_documents_count = sum(documents_count_by_resourcetype.values())
    donut = [
        {   'source': key, 
            'count': value,
            'part' : round(value * 100 / total_documents_count) if total_documents_count else 0,
        }
        for key, value in documents_count_by_resourcetype.items()
    ]

    # deal with the form
    if request.method == 'POST':
        # fomr validation
        form = CustomForm(request.POST, request.FILES)
        if form.is_valid():
            # extract information from the form
            name = form.cleaned_data['name']
            thefile = form.cleaned_data['file']
            resourcetype = cache.ResourceType[form.cleaned_data['type']]
            # which default language shall be used?
            if resourcetype.name == "europress_french":
                language_id = cache.Language['fr'].id
            elif resourcetype.name == "europress_english":
                language_id = cache.Language['en'].id
            else:
                language_id = None
            # corpus node instanciation as a Django model
            from node import models
            dj_corpus = models.Node(
                name = name,
                user_id = request.user.id,
                parent_id = project_id,
                type_id = cache.NodeType['Corpus'].id,
                language_id = language_id,
            )
            dj_corpus.save()
            # add the uploaded resource to the corpus
            dj_corpus.add_resource(
                user_id = request.user.id,
                type_id = resourcetype.id,
                file = thefile,
            )
            # let's start the workflow
            try:
                parse_resources(dj_corpus, user_id=request.user.id)
                # if DEBUG is True:
                #     dj_corpus.workflow()
                # else:
                #     dj_corpus.workflow.apply_async((), countdown=3)
            except Exception as error:
                print('WORKFLOW ERROR')
                print(error)
            # redirect to the main project page
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