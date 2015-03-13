from django.shortcuts import redirect
from django.shortcuts import render

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context

from node import models
from node.models import Language, ResourceType, Resource, \
        Node, NodeType, Node_Resource, Project, Corpus, \
        Ngram, Node_Ngram, NodeNgramNgram, NodeNodeNgram

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

from gargantext_web.settings import DEBUG, STATIC_ROOT
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
    return HttpResponse(svg_data, mimetype="image/svg+xml")

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

    #projects = Node.objects.filter(user=user, type_id = project_type.id).order_by("-date")
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


def project(request, project_id):
    '''
    This view represents all corpora in a panoramic way.
    The title sums all corpora
    The donut summerizes composition of the project.
    The list of lists enalbles to navigate throw it.
    '''

    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = str(project_id)
    except ValueError:
        raise Http404()
    user = request.user
    date = datetime.datetime.now()
    
    type_corpus     = NodeType.objects.get(name='Corpus')
    type_document   = NodeType.objects.get(name='Document')
    
#    type_whitelist  = NodeType.objects.get(name='WhiteList')
#    type_blacklist  = NodeType.objects.get(name='BlackList')
#    type_cooclist   = NodeType.objects.get(name='Cooccurrence')

    project = Node.objects.get(id=project_id)
    corpora = Node.objects.filter(parent=project, type=type_corpus)
    number  = len(corpora)

    # DONUT corpora representation
    list_corpora    = defaultdict(list)
    donut_part      = defaultdict(int)
    docs_total      = 0
    
    # List of resources
    # filter for each project here
    whitelists      = ""#.children.filter(type=type_whitelist)
    blacklists      = ""#.children.filter(type=type_blacklist)
    cooclists       = ""#.children.filter(type=type_cooclist)
    
    for corpus in corpora:
        docs_count =  Node.objects.filter(parent=corpus, type=type_document).count()
        # print("corpus:", corpus.pk , " | name:",corpus.name , " | type:",corpus.type_id , " | #docs:",docs_count)
        docs_total += docs_count
        
        corpus_view = dict()
        corpus_view['id']         = corpus.pk
        corpus_view['name']       = corpus.name
        corpus_view['count']      = docs_count

        #just get first element of the corpora and get his type.

        resource_corpus = Node_Resource.objects.filter(node=corpus)
        if len(resource_corpus)>0:
            # print(Node_Resource.objects.filter(node=corpus).all())
            corpus_type = Node_Resource.objects.filter(node=corpus)[0].resource.type
            list_corpora[corpus_type].append(corpus_view)
            donut_part[corpus_type] += docs_count
        else: print(" Node_Resource = this.corpus(",corpus.pk,") ... nothing, why?")

        ## For avoiding to list repeated elements, like when u use the dynamic query (per each xml, 1)
        # for node_resource in Node_Resource.objects.filter(node=corpus):
        #     print( "node_resource.id:",node_resource.id , node_resource.resource.file )
        #     donut_part[node_resource.resource.type] += docs_count
        #     list_corpora[node_resource.resource.type.name].append(corpus_view)
            # print(node_resource.resource.type.name)
    list_corpora = dict(list_corpora)

    if docs_total == 0 or docs_total is None:
        docs_total = 1
    # The donut will show: percentage by  
    donut = [ {'source': key, 
                'count': donut_part[key] , 
                'part' : round(donut_part[key] * 100 / docs_total) } \
                        for key in donut_part.keys() ]

    dauser = User.objects.get( username=user )
    groups = len(dauser.groups.filter(name="PubMed_0.1"))
    print("*groupslen*:",groups)

    if request.method == 'POST':

        form = CustomForm(request.POST, request.FILES)

        if form.is_valid():
            name = form.cleaned_data['name']
            thefile = form.cleaned_data['file']
            resource_type = ResourceType.objects.get(name=str( form.cleaned_data['type'] ))

            print("-------------")
            print(name,"|",resource_type,"|",thefile)
            print("-------------")

            try:
                parent      = Node.objects.get(id=project_id)
                node_type   = NodeType.objects.get(name='Corpus')
                
                if resource_type.name == "europress_french":
                    language    = Language.objects.get(iso2='fr')
                elif resource_type.name == "europress_english":
                    language    = Language.objects.get(iso2='en')
                
                try:
                    corpus = Node(
                            user=request.user,
                            parent=parent,
                            type=node_type,
                            language=language,
                            name=name,
                            )
                except:
                    corpus = Node(
                            user=request.user,
                            parent=parent,
                            type=node_type,
                            name=name,
                            )
                corpus.save()
                corpus.add_resource(
                        user=request.user,
                        type=resource_type,
                        file=thefile
                        )

                try:
                    #corpus.parse_and_extract_ngrams()
                    #corpus.parse_and_extract_ngrams.apply_async((), countdown=3)
                    if DEBUG is True:
                        corpus.workflow()
                    else:
                        corpus.workflow.apply_async((), countdown=3)

                except Exception as error:
                    print(error)

                return HttpResponseRedirect('/project/' + str(project_id))

            except Exception as error:
                print('ee', error)
                form = CorpusForm(request=request)
                formResource = ResourceForm()

        else:
            print("bad form, bad form")
            return render(request, 'project.html', {
                    'form'          : form,
                    'user'          : user,
                    'date'          : date,
                    'project'       : project,
                    'donut'         : donut,
                    'list_corpora'  : list_corpora,
                    'whitelists'    : whitelists,
                    'blacklists'    : blacklists,
                    'cooclists'     : cooclists,
                    'number'        : number,
                })
    else:
        form = CustomForm()
  
    return render(request, 'project.html', {
            'form'          : form,
            'user'          : user,
            'date'          : date,
            'project'       : project,
            'donut'         : donut,
            'list_corpora'  : list_corpora,
            'whitelists'    : whitelists,
            'blacklists'    : blacklists,
            'cooclists'     : cooclists,
            'number'        : number,
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

    t = get_template('subcorpus.html')
    
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

def delete_node(request, node_id):

    #nodes = session.query(Node).filter(or_(Node.id == node_id, Node.parent_id == node_id)).all()
    node = session.query(Node).filter(Node.id == node_id).first()
    session.delete(node)
    session.flush()
    
    if node.type_id == cache.NodeType['Project'].id:
        return HttpResponseRedirect('/projects/')
    elif node.type_id == cache.NodeType['Corpus'].id:
        return HttpResponseRedirect('/project/' + node_id)


def delete_corpus(request, project_id, node_id):
    node = session.query(Node).filter(Node.id == node_id).first()
    session.delete(node)
    session.commit()
    session.flush()
    
    return HttpResponseRedirect('/project/' + project_id)

def chart(request, project_id, corpus_id):
    ''' Charts to compare, filter, count'''
    t = get_template('chart.html')
    user = request.user
    date = datetime.datetime.now()
    
    project = Node.objects.get(id=project_id)
    corpus  = Node.objects.get(id=corpus_id)
    
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
    
    project = Node.objects.get(id=project_id)
    corpus = Node.objects.get(id=corpus_id)

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
    
    project = Node.objects.get(id=project_id)
    corpus = Node.objects.get(id=corpus_id)

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

    corpus = Node.objects.get(id=corpus_id)
    type_document = NodeType.objects.get(name="Document")
    documents = Node.objects.filter(parent=corpus, type=type_document)

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
from gargantext_web.settings import MEDIA_ROOT
def node_link(request, corpus_id):
    '''
    Create the HttpResponse object with the node_link dataset.
    '''   

    data = []
    
    corpus = Node.objects.get(id=corpus_id)
    filename = MEDIA_ROOT + '/corpora/%s/%s_%s.json' % (request.user , corpus.parent.id, corpus_id)
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
