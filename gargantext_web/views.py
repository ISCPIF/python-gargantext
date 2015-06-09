from django.shortcuts import redirect
from django.shortcuts import render
from django.db import transaction

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template.loader import get_template
from django.template import Context

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

from django.http import *
from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from scrappers.scrap_pubmed.admin import Logger

from gargantext_web.db import *

from sqlalchemy import or_, func

from gargantext_web import about



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
        color = "#ff8080"
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
    sponsors    = about.get_sponsors()

    html = template.render(Context({\
            'user': user,\
            'date': date,\
            'team': members,\
            'sponsors':sponsors,\
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

    projects = session.query(Node).filter(Node.user_id == user_id, Node.type_id == project_type_id).order_by(Node.date).all()

    number = len(projects)

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
        'projects': projects
        })

def corpus(request, project_id, corpus_id):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = int(project_id)
        offset = int(corpus_id)
    except ValueError:
        raise Http404()

    t = get_template('corpus.html')

    user = request.user
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
    print('processing', processing)

    html = t.render(Context({
            'debug': settings.DEBUG,
            'user': user,
            'date': date,
            'project': project,
            'corpus' : corpus,
            'processing' : processing,
#            'documents': documents,\
            'number' : number,
            }))

    return HttpResponse(html)


def newpaginatorJSON(request , corpus_id):

    results = ["hola" , "mundo"]

    # t = get_template('tests/newpag/thetable.html')

    # project = session.query(Node).filter(Node.id==project_id).first()
    corpus  = session.query(Node).filter(Node.id==corpus_id).first()
    type_document_id = cache.NodeType['Document'].id
    user_id = request.user.id
    # documents  = session.query(Node).filter(Node.parent_id==corpus_id , Node.type_id == type_document_id ).all()

    documents  = session.query(Node).filter(Node.user_id == user_id , Node.parent_id==corpus_id , Node.type_id == type_document_id ).all() 

    # for doc in documents:
    #     print(doc.name)
    #     if "publication_date" in doc.hyperdata:
    #         print(doc.hyperdata["publication_date"])
    #     else: print ("No date")
    #     print(" - - - - - -   -")

    # print(" = = = = = = = = = = = = = = = == = = = ")
    filtered_docs = []
    for doc in documents:
        if "publication_date" in doc.hyperdata:
            try:
                realdate = doc.hyperdata["publication_date"].split(" ")[0] # in database is = (year-month-day = 2015-01-06 00:00:00 = 06 jan 2015 00 hrs)
                realdate = datetime.datetime.strptime(str(realdate), '%Y-%m-%d').date() # finalform = (yearmonthday = 20150106 = 06 jan 2015)
                # doc.date = realdate
                resdict = {}
                resdict["id"] = doc.id
                resdict["date"] = realdate
                resdict["name"] =  doc.name
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


def empty_trash():
    nodes = models.Node.objects.filter(type_id=cache.NodeType['Trash'].id).all()
    with transaction.atomic():
        for node in nodes:
            try:
                node.children.delete()
            except Exception as error:
                print(error)

            node.delete()


def move_to_trash(node_id):
    try:
        node = session.query(Node).filter(Node.id == node_id).first()

        previous_type_id = node.type_id
        node.type_id = cache.NodeType['Trash'].id

        session.add(node)
        session.commit()
        return(previous_type_id)
    except Exception as error:
        print("can not move to trash Node" + node_id + ":" + error)



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

    previous_type_id = move_to_trash(node_id)

    if previous_type_id == cache.NodeType['Corpus'].id:
        return HttpResponseRedirect('/project/' + str(node.parent_id))
    else:
        return HttpResponseRedirect('/projects/')


    if settings.DEBUG == True:
        empty_trash()



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

def graph(request, project_id, corpus_id):
    t = get_template('explorer.html')
    user = request.user
    date = datetime.datetime.now()

    project = session.query(Node).filter(Node.id==project_id).first()
    corpus  = session.query(Node).filter(Node.id==corpus_id).first()


    user_id         = cache.User[request.user.username].id
    project_type_id = cache.NodeType['Project'].id
    corpus_type_id = cache.NodeType['Corpus'].id

    results = {}
    projs = session.query(Node).filter(Node.user_id == user_id,Node.type_id==project_type_id).all()
    for i in projs:
        # print(i.id , i.name)
        if i.id not in results: results[i.id] = {}
        results[i.id]["proj_name"] = i.name
        results[i.id]["corpuses"] = []
        corpuses = session.query(Node).filter(Node.parent_id==i.id , Node.type_id==corpus_type_id).all()
        for j in corpuses:
            if int(j.id)!=int(corpus_id):
                info = { "id":j.id , "name":j.name }
                results[i.id]["corpuses"].append(info)
                # print("\t",j.id , j.name)

    import pprint
    pprint.pprint(results)

    html = t.render(Context({\
            'debug': settings.DEBUG,
            'user'      : user,\
            'date'      : date,\
            'corpus'    : corpus,\
            'project'   : project,\
            'corpusinfo'   : results,\
            'graphfile' : "hola_mundo",\
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

    keys = list(documents[0].hyperdata.keys())
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
from gargantext_web.api import JsonHttpResponse
from analysis.functions import get_cooc
def node_link(request, corpus_id):
    '''
    Create the HttpResponse object with the node_link dataset.
    '''

    data = []

    corpus = session.query(Node).filter(Node.id==corpus_id).first()
    filename = settings.MEDIA_ROOT + '/corpora/%s/%s_%s.json' % (request.user , corpus.parent_id, corpus_id)
    print("file exists?:",os.path.isfile(filename))
    if os.path.isfile(filename):
        json_data = open(filename,"r")
        data = json.load(json_data)
        json_data.close()
    else:
        data = get_cooc(request=request, corpus_id=corpus_id, type="node_link")
    return JsonHttpResponse(data)

def adjacency(request, corpus_id):
    '''
    Create the HttpResponse object with the adjacency dataset.
    '''
    data = get_cooc(request=request, corpus_id=corpus_id, type="adjacency")
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
