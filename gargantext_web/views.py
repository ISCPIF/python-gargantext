from admin.utils import PrintException
from django.shortcuts import redirect, render, render_to_response

from django.db import transaction

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template.loader import get_template
from django.template import Context, RequestContext

# remove this
from node import models
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

# SOME FUNCTIONS

from gargantext_web import settings
from gargantext_web.settings import DEBUG

from django.http import *
from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from scrappers.scrap_pubmed.admin import Logger


from sqlalchemy import or_, func

from gargantext_web import about
from gargantext_web.celery import empty_trash

from gargantext_web.db import *
from gargantext_web.db import session, cache, NodeNgram, NodeNgramNgram

def login_user(request):
    logout(request)
    username = password = ''
    print(request)
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:

            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/projects/')
    return render_to_response('authentication.html', context_instance=RequestContext(request))

def logout_user(request):
    logout(request)
    return HttpResponseRedirect('/')
    # Redirect to a success page.

def logo(request):
    template = get_template('logo.svg')
    group = "mines"
    #group = "cnrs"
    if group == "cnrs":
        color = "#093558"
    else:
        # color of the css adapted to the logo
        color = "#AE5C5C"
    svg_data = template.render(Context({\
            'color': color,\
            }))
    return HttpResponse(svg_data, content_type="image/svg+xml")

def css(request):
    template = get_template('bootstrap.css')
    css = dict()
    group = "mines"
    #group = "cnrs"

    if group == "mines":
        css['color']        = '#666666'
        css['background']   = '#f8f8f7'
        css['a']            = '#bd2525'
        css['focus']        = '#7d1818'
        css['hr']           = '#eaafae'
        css['text']         = '#a2a3a2'
        css['form']         = '#a5817f'
        css['help']         = '#a6a6a6'
    else:
        css['color']        = '#E2E7EB'
        css['background']   = '#8C9DAD' #container background
        css['a']            = '#093558'
        css['focus']        = '#556F86'
        css['hr']           = '#426A8A'
        css['text']         = '#214A6D'
        css['form']         = '#093558'
        css['help']         = '#093558'

    css_data = template.render(Context({\
            'css': css,\
            }))
    return HttpResponse(css_data, mimetype="text/css")

def query_to_dicts(query_string, *query_args):
    """Run a simple query and produce a generator
    that returns the results as a bunch of dictionaries
    with keys for the column values selected.
    """
    cursor = connection.cursor()
    cursor.execute(query_string, query_args)
    col_names = [desc[0] for desc in cursor.description]
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        row_dict = dict(zip(col_names, row))
        yield row_dict
    return

def date_range(start_dt, end_dt = None, format=None):
    if format is None:
        form = "%Y-%m-%d"
        d = 1

    elif format == "years":
        form = "%Y"
        d = 365

    elif format == "months":
        form = "%Y-%m"
        d = 30

    elif format == "days":
        form = "%Y-%m-%d"
        d = 1

    start_dt = datetime.datetime.strptime(start_dt, form)
    if end_dt: end_dt = datetime.datetime.strptime(end_dt, form)
    while start_dt <= end_dt:
        yield start_dt.strftime(form)
        start_dt += datetime.timedelta(days=d)

# SOME VIEWS

def get_about(request):
    '''
    About Gargantext, the team and sponsors
    '''
    template    = get_template('about.html')
    user        = request.user
    date        = datetime.datetime.now()

    members     = about.get_team()
    institutions,labos,grants    = about.get_partners()

    html = template.render(Context({\
            'user': user,\
            'date': date,\
            'team': members,\
            'institutions': institutions,\
            'labos': labos,\
            'grants': grants,\
            }))

    return HttpResponse(html)

def get_maintenance(request):
    '''
    Gargantext out of service
    '''
    template    = get_template('maintenance.html')
    user        = request.user
    date        = datetime.datetime.now()

    html = template.render(Context({\
            'user': user,\
            'date': date,\
            }))

    return HttpResponse(html)

from gargantext_web import home
def home_view(request):
    '''
    Home describes the platform.
    A video draws the narratives.
    If not logged a project test is shown.
    '''
    t = get_template('home.html')
    user = request.user
    date = datetime.datetime.now()
    html = t.render(Context({
            'debug': settings.DEBUG,
            'user': user,
            'date': date,
            'paragraph_gargantua': home.paragraph_gargantua(),
            'paragraph_lorem' : home.paragraph_lorem(),
            'paragraph_tutoreil': home.paragraph_tutoreil(),
            }))

    return HttpResponse(html)

def projects(request):
    '''
    This view show all projects for each user.
    Each project is described with hyperdata that are updateded on each following view.
    To each project, we can link a resource that can be an image.
    '''
    if not request.user.is_authenticated():
        return redirect('/auth/')

    t = get_template('projects.html')

    user_id         = cache.User[request.user.username].id
    project_type_id = cache.NodeType['Project'].id

    date = datetime.datetime.now()
    # print(Logger.write("STATIC_ROOT"))
    
    # implicit global session
    projects = session.query(Node).filter(Node.user_id == user_id, Node.type_id == project_type_id).order_by(Node.date).all()
    number = len(projects)
    

    # common_users = session.query(User_User.user_parent).filter( User_User.user_id==user_id ).all()
    # [ Getting shared projects ] #
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

    for u in common_users:
        u_id = u[0]
        u_name = u[1]
        shared_projects = session.query(Node).filter(Node.user_id == u_id, Node.type_id == project_type_id).order_by(Node.date).all()
        print("admin group user ID:",u_id , " | nb_projects:",len(shared_projects))
        if len(shared_projects)>0:
            for p in shared_projects:
                common_projects.append( p )

    if len(common_projects)==0:
        common_projects = False
    if len(common_users)==0:
        common_users = False
    # [ / Getting shared projects ] #

    form = ProjectForm()
    if request.method == 'POST':
        # form = ProjectForm(request.POST)
        # TODO : protect from sql injection here
        name = str(request.POST['name'])
        if name != "" :
            new_project = Project(name=name, type_id=project_type_id, user_id=user_id)
            session.add(new_project)
            session.commit()
            return HttpResponseRedirect('/projects/')
    else:
        form = ProjectForm()
    
    return render(request, 'projects.html', {
        'debug': settings.DEBUG,
        'date': date,
        'form': form,
        'number': number,
        'projects': projects,
        'common_projects':common_projects,
        'common_users':common_users,
        })
    

def update_nodes(request, project_id, corpus_id, view=None):
    '''
    update function:
        - remove previous computations (temporary lists and coocurrences)
        - permanent deletion of Trash

    '''
    
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = int(project_id)
        offset = int(corpus_id)
        if view is not None:
            offset = str(view)
    except ValueError:
        raise Http404()

    try:
        print(corpus_id)
        whites = (session.query(Node)
                .filter(Node.parent_id==corpus_id)
                .filter(Node.type_id  == cache.NodeType['WhiteList'].id)
                .all()
                )
        print(whites)
        for white in whites:
            session.query(NodeNgram).filter(NodeNgram.node_id==white.id).delete()
            session.delete(white)

        cooc = (session.query(Node)
                .filter(Node.parent_id==corpus_id)
                .filter(Node.type_id  == cache.NodeType['Cooccurrence'].id)
                .first()
                )

        session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooc.id).delete()
        session.delete(cooc)
        session.commit()
    except :
        PrintException()

    nodes = models.Node.objects.filter(type_id=cache.NodeType['Trash'].id, user_id=request.user.id).all()

    if nodes is not None:
        with transaction.atomic():
            for node in nodes:
                try:
                    node.children.delete()
                except Exception as error:
                    print(error)

                node.delete()


    #return redirect(request.path.replace('update', ''))
    if view is None:
        return redirect('/project/%s/corpus/%s/' % (project_id, corpus_id))
    else:
        return redirect('/project/%s/corpus/%s/%s' % (project_id, corpus_id, view))
#
#    return render_to_response(
#            request.path,
#            { 'title': 'Corpus view' },
#            context_instance=RequestContext(request)
#        )
#

def corpus(request, project_id, corpus_id):
    
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = int(project_id)
        offset = int(corpus_id)
    except ValueError:
        raise Http404()

    t = get_template('corpus/documents.html')

    date = datetime.datetime.now()

    project = cache.Node[int(project_id)]
    corpus  = cache.Node[int(corpus_id)]

    type_doc_id = cache.NodeType['Document'].id
    
    # implicit global session
    number = session.query(func.count(Node.id)).filter(Node.parent_id==corpus_id, Node.type_id==type_doc_id).all()[0][0]


    # [ getting workflow status ] #
    the_query = """ SELECT hyperdata FROM node_node WHERE id=%d """ % ( int(corpus_id) )
    cursor = connection.cursor()
    try:
        cursor.execute(the_query)
        processing = cursor.fetchone()[0]["Processing"]
    except:
        processing = "Error"
    # [ / getting workflow status ] #

    html = t.render(Context({
            'debug': settings.DEBUG,
            'user': request.user,
            'date': date,
            'project': project,
            'corpus' : corpus,
            'processing' : processing,
#            'documents': documents,\
            'number' : number,
            'view'   : "documents"
            }))

    return HttpResponse(html)

def newpaginatorJSON(request , corpus_id):

    
    # t = get_template('tests/newpag/thetable.html')

    # project = session.query(Node).filter(Node.id==project_id).first()
    corpus  = session.query(Node).filter(Node.id==corpus_id).first()
    type_document_id = cache.NodeType['Document'].id
    user_id = request.user.id
    # documents  = session.query(Node).filter(Node.parent_id==corpus_id , Node.type_id == type_document_id ).all()

    docs  = (session.query(Node)
                .filter(Node.parent_id==corpus_id 
                , Node.type_id == type_document_id )
                .all()
            )

    # for doc in documents:
    #     print(doc.name)
    #     if "publication_date" in doc.hyperdata:
    #         print(doc.hyperdata["publication_date"])
    #     else: print ("No date")
    #     print(" - - - - - -   -")

    # print(" = = = = = = = = = = = = = = = == = = = ")
    filtered_docs = []
    for doc in docs:
        if "publication_date" in doc.hyperdata:
            try:
                realdate = doc.hyperdata["publication_date"].replace('T',' ').split(" ")[0] # in database is = (year-month-day = 2015-01-06 00:00:00 = 06 jan 2015 00 hrs)
                realdate = datetime.datetime.strptime(str(realdate), '%Y-%m-%d').date() # finalform = (yearmonthday = 20150106 = 06 jan 2015)
                # doc.date = realdate
                resdict = {}
                resdict["id"] = doc.id
                resdict["date"] = realdate
                resdict["name"] =  ""
                if doc.name and doc.name!="":
                    resdict["name"] = doc.name
                else:
                    resdict["name"] = doc.hyperdata["doi"]

                filtered_docs.append( resdict )
            except Exception as e:
                print ("pag2 error01 detail:",e)
                print("pag2 error01 doc:",doc)
    results = sorted(filtered_docs, key=lambda x: x["date"])
    for i in results:
        i["date"] = i["date"].strftime("%Y-%m-%d")
        # print( i["date"] , i["id"] , i["name"])

    finaldict = {
        "records":results,
        "queryRecordCount":10,
        "totalRecordCount":len(results)
    }
    return JsonHttpResponse(finaldict)

def move_to_trash(node_id):
    try:
        node = session.query(Node).filter(Node.id == node_id).first()

        previous_type_id = node.type_id
        node.type_id = cache.NodeType['Trash'].id

        session.add(node)
        session.commit()
        
        if DEBUG is False :
            # TODO for the future maybe add id of node
            empty_trash.apply_async([1,])
        else:
            empty_trash("corpus_id")

        #return(previous_type_id)
    except Exception as error:
        print("can not move to trash Node" + str(node_id) + ":" + str(error))
    

def move_to_trash_multiple(request):
    
    user = request.user
    
    if not user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    results = ["operation","failed"]

    if request.method == "POST":
        nodes2trash = json.loads(request.POST["nodeids"])
        print("nodes to the trash:")
        print(nodes2trash)
        nodes = session.query(Node).filter(Node.id.in_(nodes2trash)).all()
        for node in nodes:
            node.type_id = cache.NodeType['Trash'].id
            session.add(node)

        session.commit()

        results = ["tudo","fixe"]

    return JsonHttpResponse(results)

def delete_node(request, node_id):

    
    # do we have a valid user?
    user = request.user
    
    node = session.query(Node).filter(Node.id == node_id).first()

    if not user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)
    if node.user_id != user.id:
        return HttpResponseForbidden()

    previous_type_id = node.type_id
    node_parent_id   = node.parent_id
    move_to_trash(node_id)

    if previous_type_id == cache.NodeType['Corpus'].id:
        return HttpResponseRedirect('/project/' + str(node_parent_id))
    else:
        return HttpResponseRedirect('/projects/')
    

def delete_corpus(request, project_id, node_id):
    # ORM Django
    with transaction.atomic():
        node = models.Node.objects.get(id=node_id)
        try:
            node.children.delete()
        except Exception as error:
            print(error)
        node.delete()

    # SQLA Django
#    node = session.query(Node).filter(Node.id == node_id).first()
#    session.delete(node)
#    session.commit()
#    session.flush()

    return HttpResponseRedirect('/project/' + project_id)

def chart(request, project_id, corpus_id):
    ''' Charts to compare, filter, count'''
    
    t = get_template('chart.html')
    user = request.user
    date = datetime.datetime.now()

    project = session.query(Node).filter(Node.id==project_id).first()
    corpus  = session.query(Node).filter(Node.id==corpus_id).first()

    html = t.render(Context({
        'debug': settings.DEBUG,
        'user'      : user,
        'date'      : date,
        'project'   : project,
        'corpus'    : corpus,
    }))
    return HttpResponse(html)

def sankey(request, corpus_id):
    
    t = get_template('sankey.html')
    user = request.user
    date = datetime.datetime.now()

    corpus =  session.query(Node).filter(Node.id==corpus_id).first()

    html = t.render(Context({\
            'debug': settings.DEBUG,
            'user'      : user,\
            'date'      : date,\
            'corpus'    : corpus,\
            }))

    return HttpResponse(html)


def matrix(request, project_id, corpus_id):
    t = get_template('matrix.html')
    user = request.user
    date = datetime.datetime.now()

    project = session.query(Node).filter(Node.id==project_id).first()
    corpus =  session.query(Node).filter(Node.id==corpus_id).first()

    html = t.render(Context({\
            'debug': settings.DEBUG,
            'user'      : user,\
            'date'      : date,\
            'corpus'    : corpus,\
            'project'   : project,\
            }))

    return HttpResponse(html)

def graph(request, project_id, corpus_id, generic=100, specific=100):
    
    t = get_template('explorer.html')
    user = request.user
    date = datetime.datetime.now()

    project = session.query(Node).filter(Node.id==project_id).first()
    corpus  = session.query(Node).filter(Node.id==corpus_id).first()


    user_id         = cache.User[request.user.username].id
    project_type_id = cache.NodeType['Project'].id
    corpus_type_id = cache.NodeType['Corpus'].id

    miamlist_type_id = cache.NodeType['MiamList'].id
    miamlist = session.query(Node).filter(Node.user_id == request.user.id , Node.parent_id==corpus_id , Node.type_id == cache.NodeType['MiamList'].id ).first()

    graphurl = "corpus/"+str(corpus_id)+"/node_link.json"

    html = t.render(Context({\
            'debug': settings.DEBUG,
            'user': request.user,\
            'date'      : date,\
            'corpus'    : corpus,\
            'list_id'    : miamlist.id,\
            'project'   : project,\
            'graphfile' : graphurl,\
            }))

    return HttpResponse(html)

def exploration(request):
    t = get_template('exploration.html')
    user = request.user
    date = datetime.datetime.now()

    html = t.render(Context({\
            'debug': settings.DEBUG,
            'user': user,\
            'date': date,\
            }))

    return HttpResponse(html)

def explorer_chart(request):
    t = get_template('chart.html')
    user = request.user
    date = datetime.datetime.now()

    html = t.render(Context({\
            'debug': settings.DEBUG,
            'user': user,\
            'date': date,\
            }))

    return HttpResponse(html)

import csv
from django.db import connection

def corpus_csv(request, project_id, corpus_id):
    '''
    Create the HttpResponse object with the appropriate CSV header.
    '''
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="corpus.csv"'

    writer = csv.writer(response)

    corpus_id = session.query(Node.id).filter(Node.id==corpus_id).first()
    type_document_id = cache.NodeType['Document'].id
    documents = session.query(Node).filter(Node.parent_id==corpus_id, Node.type_id==type_document_id).all()

    keys_list = list()
    for d in documents[:10]:
        keys_list += d.hyperdata.keys()
    keys = list(set(keys_list))

    writer.writerow(keys)

    for doc in documents:
        data = list()
        for key in keys:
            try:
                data.append(doc.hyperdata[key])
            except:
                data.append("")
        writer.writerow(data)


    return response

def send_csv(request, corpus_id):
    '''
    Create the HttpResponse object with the appropriate CSV header.
    '''
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="data.csv"'

    writer = csv.writer(response)
    cursor = connection.cursor()

    cursor.execute("""
    SELECT
        hyperdata ->> 'publication_year' as year,
        hyperdata ->> 'publication_month' as month,
        hyperdata ->> 'publication_day' as day,
        COUNT(*)
    FROM
        node_node AS n
    WHERE
        n.parent_id = %s
    GROUP BY
        day, month, year
    ORDER BY
        year, month, day ASC
    """, [corpus_id])

    writer.writerow(['date','volume'])

    while True:
        row = cursor.fetchone()
        if row is None:
            break
        if row[0] is not None and row[1] is not None and row[2] is not None and row[3] is not None:
            writer.writerow([ str(row[0]) + '/' + str(row[1]) + '/' + str(row[2])  , str(row[3]) ])
        #dates['last']['day'] = documents.last().hyperdata['publication_day'])

    cursor.close()

    return response

# To get the data
from rest_v1_0.api import JsonHttpResponse,CsvHttpResponse
from analysis.functions import get_cooc
def node_link(request, corpus_id):
    '''
    Create the HttpResponse object with the node_link dataset.
    '''
    data = []
    corpus = session.query(Node).filter(Node.id==corpus_id).first()
    data = get_cooc(request=request, corpus=corpus, type="node_link")
    return JsonHttpResponse(data)

from analysis.periods import phylo_clusters

def sankey_csv(request, corpus_id):
    
    data = []
    corpus = session.query(Node).filter(Node.id==corpus_id).first()
#
#    header = ["source", "target", "value"] 
#    data.append(header)
#    
#    flows = phylo_clusters(corpus, range(2005,2013)) 
#    for flow in flows: 
#        data.append(flow) 
#    print(data)
#

    data = [
              ['source', 'target', 'value']
            , ['inégalités,rapports sociaux,P1', 'critique,travail social,P2', 8]
            , ['inégalités,rapports sociaux,P1', 'inégalités,éducation,P2', 21]
            , ['éducation,institutions,P1', 'critique,travail social,P2', 7]
            , ['éducation,institutions,P1', 'inégalités,éducation,P2', 10]
            #, ['éducation,institutions,P1', 'personnes âgées,pouvoirs publics,P2', 8]
            , ['éducation,institutions,P1', 'politiques publiques,personnes âgées dépendantes,P2', 8]
            #, ['éducation,institutions,P1', 'intervention sociale,travailleur social,P2', 8]
            #, ['intervention sociale,travailleur social,2011-01-01 2013-12-31', 'intervention sociale,travailleur social,P3', 0]
            , ['critique,enseignement supérieur,P1', 'critique,travail social,P2', 6]
            #, ['critique,enseignement supérieur,P1', 'personnes âgées,pouvoirs publics,P2', 7]
            , ['justice,exclusion,violence,P1', 'inégalités,éducation,P2', 12]
            , ['critique,travail social,P2', 'justice,travail social,P3', 14]
            , ['inégalités,éducation,P2', 'justice,travail social,P3', 20]
            , ['inégalités,éducation,P2', 'justice sociale,éducation,P3', 8]
            , ['inégalités,éducation,P2', 'action publique,institutions,P3', 9]
            , ['inégalités,éducation,P2', 'inégalités,inégalités sociales,P3', 18]
            , ['politiques publiques,personnes âgées dépendantes,P2', 'justice sociale,éducation,P3', 20]
            ]

    return(CsvHttpResponse(data))

def adjacency(request, corpus_id):
    '''
    Create the HttpResponse object with the adjacency dataset.
    '''
    data = get_cooc(request=request, corpus=corpus, type="adjacency")
    return JsonHttpResponse(data)

def graph_it(request):
    '''The new multimodal graph.'''
    t = get_template('graph-it.html')
    user = request.user
    date = datetime.datetime.now()
    html = t.render(Context({
        'user': user,
        'date': date,
    }))
    return HttpResponse(html)

def tests_mvc(request):
    '''Just a test page for Javascript MVC.'''
    t = get_template('tests/mvc.html')
    user = request.user
    date = datetime.datetime.now()
    html = t.render(Context({
        'user': user,
        'date': date,
    }))
    return HttpResponse(html)

def tests_mvc_listdocuments(request):
    '''Just a test page for Javascript MVC.'''
    t = get_template('tests/mvc-listdocuments.html')
    user = request.user
    date = datetime.datetime.now()
    html = t.render(Context({
        'user': user,
        'date': date,
    }))
    return HttpResponse(html)

def ngrams(request):
    '''The ngrams list.'''
    t = get_template('ngrams.html')
    ngrams_list = list()

    for node_ngram in Node_Ngram.objects.filter(node_id=81246)[:20]:
        ngrams_list.append(node_ngram.ngram)

    user = request.user
    date = datetime.datetime.now()
    html = t.render(Context({
        'user': user,
        'date': date,
        'ngrams' : ngrams_list,
    }))
    return HttpResponse(html)

def nodeinfo(request , node_id):
    '''Structure of the popUp for topPapers div '''
    t = get_template('node-info.html')
    ngrams_list = ["hola","mundo"]

    user = request.user
    date = datetime.datetime.now()
    html = t.render(Context({
        'user': user,
        'date': date,
        'node_id' : node_id,
    }))
    return HttpResponse(html)
