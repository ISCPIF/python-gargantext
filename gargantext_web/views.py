from django.shortcuts import redirect
from django.shortcuts import render
from django.db import transaction

from django.http import Http404, HttpResponse, HttpResponseRedirect, HttpResponseForbidden
from django.template.loader import get_template
from django.template import Context

from node import models
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

# SOME FUNCTIONS

from gargantext_web import settings

from django.http import *
from django.shortcuts import render_to_response,redirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from scrap_pubmed.admin import Logger

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
    html = t.render(Context({\
            'user': user,\
            'date': date,\
            'paragraph_gargantua': home.paragraph_gargantua(),\
            'paragraph_lorem' : home.paragraph_lorem(),\
            'paragraph_tutoreil': home.paragraph_tutoreil(),\
            }))
    
    return HttpResponse(html)

def projects(request):
    '''
    This view show all projects for each user.
    Each project is described with metadata that are updateded on each following view.
    To each project, we can link a resource that can be an image.
    '''
    if not request.user.is_authenticated():
        return redirect('/auth/')

    t = get_template('projects.html')
    
    user_id         = cache.User[request.user.username].id
    project_type_id = cache.NodeType['Project'].id

    date = datetime.datetime.now()
    print(Logger.write("STATIC_ROOT"))
    
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
        'date': date,
        'form': form,
        'number': number,
        'projects': projects
        })


def corpus(request, project_id, corpus_id):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)
    
    try:
        offset = str(project_id)
        offset = str(corpus_id)
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
        chart = dict()
        chart['first'] = parse(corpus.children.first().metadata['publication_date']).strftime("%Y, %m, %d")
        # TODO write with sqlalchemy
        #chart['first'] = parse(session.query(Node.metadata['publication_date']).filter(Node.parent_id==corpus.id, Node.type_id==type_doc_id).first()).strftime("%Y, %m, %d")
        
        chart['last']  = parse(corpus.children.last().metadata['publication_date']).strftime("%Y, %m, %d")
        print(chart)
    except Exception as error:
        print(error)
    
    try:
        processing = corpus.metadata['Processing']
    except:
        processing = 0

    html = t.render(Context({\
            'user': user,\
            'date': date,\
            'project': project,\
            'corpus' : corpus,\
            'processing' : processing,\
#            'documents': documents,\
            'number' : number,\
            'dates' : chart,\
            }))
    
    return HttpResponse(html)


from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
def subcorpus(request, project_id, corpus_id, start , end ):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)
    try:
        offset = str(project_id)
        offset = str(corpus_id)
        offset = str(start)
        offset = str(end)
    except ValueError:
        raise Http404()

    # parameters received via web. Format = (yearmonthday = 20150106 = 06 jan 2015)
    import datetime
    dateini = datetime.datetime.strptime(str(start), '%Y%m%d').date()
    datefin = datetime.datetime.strptime(str(end), '%Y%m%d').date()
    # print (dateini,"\t",datefin)
    t = get_template('subcorpus.html')
    
    user = request.user
    date = datetime.datetime.now()
    
    project = session.query(Node).filter(Node.id==project_id).first()
    corpus  = session.query(Node).filter(Node.id==corpus_id).first()
    type_document_id = cache.NodeType['Document'].id
    # retrieving all the documents
    # documents  = corpus.children.all()
    documents  = session.query(Node).filter(Node.parent_id==corpus_id , Node.type_id == type_document_id ).all()
    number = len(documents)

    filtered_docs = []
    # filtering documents by range-date
    for doc in documents:
        if "publication_date" in doc.metadata:
            try:
                realdate = doc.metadata["publication_date"].split(" ")[0] # in database is = (year-month-day = 2015-01-06 00:00:00 = 06 jan 2015 00 hrs)
                realdate = datetime.datetime.strptime(str(realdate), '%Y-%m-%d').date() # finalform = (yearmonthday = 20150106 = 06 jan 2015)
                if dateini <= realdate <= datefin:
                    doc.date = realdate
                    filtered_docs.append(doc)
            except Exception as e:
                print ("pag error01 detail:",e)
                print("pag error01 doc:",doc)
    # import pprint
    # pprint.pprint(filtered_docs)
    # ordering from most recent to the older.
    ordered = sorted(filtered_docs, key=lambda x: x.date)


    # pages of 10 elements. Like a sir.
    paginator = Paginator(ordered, 10)

    page = request.GET.get('page')
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        results = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        results = paginator.page(paginator.num_pages)

    html = t.render(Context({\
            'user': user,\
            'date': date,\
            'project': project,\
            'corpus' : corpus,\
            'documents': results,\
            # 'number' : len(filtered_docs),\
            # 'dates' : chart,\
            }))
    
    return HttpResponse(html)


import json
def subcorpusJSON(request, project_id, corpus_id, start , end ):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)
    try:
        offset = str(project_id)
        offset = str(corpus_id)
        offset = str(start)
        offset = str(end)
    except ValueError:
        raise Http404()
    # parameters received via web. Format = (yearmonthday = 20150106 = 06 jan 2015)
    import datetime
    dateini = datetime.datetime.strptime(str(start), '%Y%m%d').date()
    datefin = datetime.datetime.strptime(str(end), '%Y%m%d').date()

    t = get_template('subcorpus.html')
    print(dateini , "\t" , datefin)
    user = request.user
    date = datetime.datetime.now()
    
    project = Node.objects.get(id=project_id)
    corpus = Node.objects.get(id=corpus_id)
    type_document = NodeType.objects.get(name="Document")
    # retrieving all the documents
    # documents  = corpus.children.all()
    documents  = corpus.__class__.objects.filter(parent_id=corpus_id , type = type_document )
    number = len(documents)

    filtered_docs = []
    # filtering documents by range-date
    for doc in documents:
        if "publication_date" in doc.metadata:
            realdate = doc.metadata["publication_date"].split(" ")[0] # in database is = (year-month-day = 2015-01-06 00:00:00 = 06 jan 2015 00 hrs)
            realdate = datetime.datetime.strptime(str(realdate), '%Y-%m-%d').date() # finalform = (yearmonthday = 20150106 = 06 jan 2015)
            if dateini <= realdate <= datefin:
                doc.date = realdate
                filtered_docs.append(doc)

    # ordering from most recent to the older.
    ordered = sorted(filtered_docs, key=lambda x: x.date)

    # pages of 10 elements. Like a sir.
    paginator = Paginator(ordered, 10)

    page = request.GET.get('page')
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        results = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        results = paginator.page(paginator.num_pages)

    from rest_framework.pagination import PaginationSerializer

    serializer = PaginationSerializer(instance=results)
    print(serializer.data)
 
    html = t.render(Context({\
            'user': user,\
            'date': date,\
            'corpus': corpus,\
            }))
    # return HttpResponse(html)
    return HttpResponse( serializer.data , content_type='application/json')


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

    html = t.render(Context({\
            'user'      : user,\
            'date'      : date,\
            'corpus'    : corpus,\
            'project'   : project,\
            'graphfile' : "hola_mundo",\
            }))
    
    return HttpResponse(html)

def exploration(request):
    t = get_template('exploration.html')
    user = request.user
    date = datetime.datetime.now()

    html = t.render(Context({\
            'user': user,\
            'date': date,\
            }))
    
    return HttpResponse(html)

def explorer_chart(request):
    t = get_template('chart.html')
    user = request.user
    date = datetime.datetime.now()

    html = t.render(Context({\
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

    keys = list(documents[0].metadata.keys())
    writer.writerow(keys)

    for doc in documents:
        data = list()
        for key in keys:
            try:
                data.append(doc.metadata[key])
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
        metadata ->> 'publication_year' as year,
        metadata ->> 'publication_month' as month,
        metadata ->> 'publication_day' as day,
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
        #dates['last']['day'] = documents.last().metadata['publication_day'])

    cursor.close()

    return response

# To get the data
from gargantext_web.api import JsonHttpResponse
from analysis.functions import get_cooc
import json
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


def tfidf2(request, corpus_id, ngram_id):
    """
    Takes IDs of corpus and ngram and returns list of relevent documents in json format
    according to TFIDF score (order is decreasing).
    """
    #it will receive something like:  api/tfidf/corpus_id/NGRAM1aNGRAM2aNGRAM3aNGRAM4...
    docsids = ngram_id.split("a")

    tfidf_list = []
    for i in docsids:
        pub = Node.objects.get(id=i)
        finalpub = {}
        finalpub["id"] = pub.id
        pubmetadata = pub.metadata
        if "title" in pubmetadata: finalpub["title"] = pubmetadata['title']
        if "publication_date" in pubmetadata: finalpub["publication_date"] = pubmetadata['publication_date']
        if "journal" in pubmetadata: finalpub["journal"] = pubmetadata['journal']
        if "authors" in pubmetadata: finalpub["authors"] = pubmetadata['authors']
        if "fields" in pubmetadata: finalpub["fields"] = pubmetadata['fields']
        tfidf_list.append(finalpub) # doing a dictionary with only available atributes
        if len(tfidf_list)==6: break # max 6 papers
    
    data = json.dumps(tfidf_list) 



    # data = ["hola","mundo"]
    return JsonHttpResponse(data)

def tfidf(request, corpus_id, ngram_id):
    """
    Takes IDs of corpus and ngram and returns list of relevent documents in json format
    according to TFIDF score (order is decreasing).
    """
    #it will receive something like:  api/tfidf/corpus_id/NGRAM1aNGRAM2aNGRAM3aNGRAM4...
    ngramsids = ngram_id.split("a")

    corpus = Node.objects.get(id=corpus_id)
    ngram  = Ngram.objects.get(id=ngramsids[0])#not used
    
    print("********web/views.tfidf*******")
    print("first ngram:")
    print(ngram)
    node_node_ngrams = NodeNodeNgram.objects.filter(nodex=corpus, ngram__in=ngramsids).order_by('-score')
    # print(node_node_ngrams)
    goodDict = {}
    for x in node_node_ngrams:
        goodDict[x.nodey.id] = x.nodey
    # print("imma here")
    # print("arguments... nodes ids:")
    # print(ngramsids)
    # print ("with tfidf:")
    # print(node_node_ngrams)
    # print("corpus:")
    # print(NodeNodeNgram.objects.filter(nodex=corpus))
    tfidf_list = []
    for x in goodDict:
        pub = goodDict[x] # getting the unique publication
        finalpub = {}
        finalpub["id"] = pub.id
        if "title" in pub.metadata: finalpub["title"] = pub.metadata['title']
        if "publication_date" in pub.metadata: finalpub["publication_date"] = pub.metadata['publication_date']
        if "journal" in pub.metadata: finalpub["journal"] = pub.metadata['journal']
        if "authors" in pub.metadata: finalpub["authors"] = pub.metadata['authors']
        if "fields" in pub.metadata: finalpub["fields"] = pub.metadata['fields']
        tfidf_list.append(finalpub) # doing a dictionary with only available atributes
        if len(tfidf_list)==6: break # max 6 papers
    
    data = json.dumps(tfidf_list) 
    return JsonHttpResponse(data)
