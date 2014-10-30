from django.shortcuts import redirect
from django.shortcuts import render

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context

#from documents.models import Project, Corpus, Document

from node.models import Language, DatabaseType, Resource
from node.models import Node, NodeType, Project, Corpus
from node.admin import CorpusForm, ProjectForm, ResourceForm

from django.contrib.auth.models import User

import datetime
from itertools import *
from django.db import connection

from django import forms

from collections import defaultdict

from parsing.FileParsers import *

# SOME FUNCTIONS

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

def home(request):
    t = get_template('home.html')
    user = request.user
    date = datetime.datetime.now()

    html = t.render(Context({\
            'user': user,\
            'date': date,\
            }))
    
    return HttpResponse(html)

def projects(request):
    if not request.user.is_authenticated():
        return redirect('/admin/logout/?next=%s' % request.path)
    
    t = get_template('projects.html')
    
    user = request.user
    date = datetime.datetime.now()
    
    project_type = NodeType.objects.get(name='Project')
    projects = Node.objects.filter(user=user, type_id = project_type.id).order_by("-date")
    number = len(projects)
 
    form = ProjectForm()
    if request.method == 'POST':
        # form = ProjectForm(request.POST)
        # TODO : protect from sql injection here
        name = str(request.POST['name'])
        if name != "" :
            Project(name=name, type=project_type, user=user).save()
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
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = str(project_id)
    except ValueError:
        raise Http404()

    user = request.user
    date = datetime.datetime.now()
    
    project = Node.objects.get(id=project_id)
    corpora = project.children.all()
    number  = project.children.count()

    board = list()
    for corpus in corpora:
        dashboard = dict()
        dashboard['id']     = corpus.pk
        dashboard['name']   = corpus.name
        dashboard['count']  = corpus.children.count()
        board.append(dashboard)


    if request.method == 'POST':
        #form = CorpusForm(request.POST, request.FILES)
        name        = str(request.POST['name'])
        try:
            language    = Language.objects.get(id=str(request.POST['language']))
        except:
            language = None

        try:
            bdd_type = DatabaseType.objects.get(id=str(request.POST['bdd_type']))
        except:
            bdd_type = None
        
        try:
            file = request.FILES['file']
        except:
            file = None

        if language is not None and name != "" and bdd_type != None and file != None :
            resource = Resource(user=request.user, guid=str(date), bdd_type=bdd_type, file=file)
            resource.save()
            node_type   = NodeType.objects.get(name='Corpus')
            parent      = Node.objects.get(id=project_id)
            
            node = Node(parent=parent, type=node_type, name=name, user=request.user, language=language)
            node.save()
            node.resource.add(resource)

            try:
                for resource in node.resource.all():
                    print(resource.bdd_type.name)
                    if resource.bdd_type.name == "PubMed":
                        fileparser = PubmedFileParser(file='/var/www/gargantext/media/' + str(resource.file))
                        fileparser.parse(node)
                    elif resource.bdd_type.name == "Web Of Science (WOS), ISI format":
                        fileparser = IsiParser(file='/var/www/gargantext/media/' + str(resource.file))
                        fileparser.parse(node)
                    elif node.bdd_type.name == "Europresse":
                        pass

            except Exception as error:
                print(error)

            return HttpResponseRedirect('/project/' + str(project_id))
        else:
            form = CorpusForm(request=request)
            formResource = ResourceForm()

    else:
        form = CorpusForm(request=request)
        formResource = ResourceForm()

    return render(request, 'project.html', {
            'form': form, 
            'formResource': formResource, 
            'user': user,
            'date': date,
            'project': project,
            'board' : board,
            'number': number,
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
    
    project = Node.objects.get(id=project_id)
    corpus  = Node.objects.get(id=corpus_id)
    
    #print(Document.objects.filter(corpus=c_id, user=request.user.pk).query)
    documents  = corpus.children
    number = corpus.children.count()

    try:
        sources = defaultdict(int)
        for document in documents.all():
            sources[document.metadata['journal']] += 1
        
        sources_donut = []
        
        for source in sources.keys():
            source_count = dict()
            source_count['count'] = source['count']
            try:
                source_count['part'] = round(source_count['count'] * 100 / number)
            except:
                source_count['part'] = None
            source_count['source'] = source['source']
            sources_donut.append(source_count)
    
    except:
        pass

    try:
        first = documents.first().date 
        last  = documents.last().date
        duree = first - last
        
        if duree.days > 365:
            date_format = 'YYYY'
            date_form = 'years'

        elif duree.days > 60:
            date_format = 'YYYY-MM'
            date_form = 'months'
        else:
            date_format = 'YYYY-MM-DD'
            date_form = 'days'

        try:
            dates = dict()

#            query_to_dicts('''select to_char(t1.date, '%s'), count(*) 
#                                from documents_document as t1
#                                INNER JOIN documents_document_corpus as t2
#                                ON (  t1.id = t2.document_id )
#                                WHERE ( t1.user_id = %d AND t2.corpus_id = %d )
#                                group by to_char(t1.date, '%s') 
#                                order by 1 DESC;''' %  (date_format, request.user.pk, int(corpus_id), date_format))
        except:
            pass
    
        
        histo = []
#        for e in date_range('1990-01', '1992-02', format=date_form):
#            print(e)
#        if date_format = 'YYYY':
#            while True:
#                if d -histo.append(d)
        for d in dates:
            histo.append(d)
         
    except:
        histo = None
       
    html = t.render(Context({\
            'user': user,\
            'date': date,\
            'project': project,\
            'corpus' : corpus,\
            'documents': documents,\
            'number' : number,\
            'sources_donut' : sources_donut,\
            'dates' : histo,\
            }))
    
    return HttpResponse(html)

def add_corpus(request):
    form = CorpusForm(request=request)
    if request.method == 'POST':
        #form = CorpusForm(request.POST, request.FILES)
        name        = str(request.POST['name'])
        
        try:
            #language    = Language.objects.get(name=str(request.POST['language']))
            language    = Language.objects.get(name='French')
        except Exception as e:
            print(e)
            language = None
        
        if name != "" :
            project_id  = 1047
            node_type   = NodeType.objects.get(name='Corpus')
            parent      = Node.objects.get(id=project_id)
            Corpus(parent=parent, type=node_type, name=name, user=request.user, language=language).save()
#            try:
#                for resource in node.resource.all():
#                    fileparser = PubmedFileParser.PubmedFileParser(file='/var/www/gargantext/media/' + str(resource.file))
#                    fileparser.parse(node)
#
#            except Exception as error:
#                print(error)

            return HttpResponseRedirect('/project/' + str(project_id))

    else:
        form = CorpusForm(request=request)

    return render(request, 'add_corpus.html', {'form': form})

def delete_project(request, node_id):
    Node.objects.filter(id=node_id).all().delete()
    return HttpResponseRedirect('/projects/')

def delete_corpus(request, project_id, corpus_id):
    Node.objects.filter(id=corpus_id).all().delete()
    return HttpResponseRedirect('/project/' + project_id)


