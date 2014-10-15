from django.shortcuts import redirect
from django.shortcuts import render

from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context

from documents.models import Project, Corpus, Document
from node.models import Node, NodeType

from django.contrib.auth.models import User

import datetime
from itertools import *
from django.db import connection

from django import forms
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
        return redirect('/login/?next=%s' % request.path)
    
    t = get_template('projects.html')
    
    user = request.user
    date = datetime.datetime.now()
    
    project = NodeType.objects.get(name='Project')
    projects = Node.objects.filter(user=user, type_id = project.id).order_by("-date")
    number = len(projects)

    html = t.render(Context({\
            'user': user,\
            'date': date,\
            'projects': projects,\
            'number': number,\
            }))
    
    return HttpResponse(html)

def project(request, project_id):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)

    try:
        offset = str(project_id)
    except ValueError:
        raise Http404()

    t = get_template('project.html')
    user = request.user

    date = datetime.datetime.now()
    
    project = Node.objects.get(id=project_id)
    corpora = project.get_children()
    number = len(corpora)

    board = list()
    for corpus in corpora:
        dashboard = dict()
        dashboard['id']     = corpus.pk
        dashboard['name']   = corpus.name
        dashboard['count']  = corpus.get_children_count()
        board.append(dashboard)

    html = t.render(Context({\
            'user': user,\
            'date': date,\
            'project': project,\
            'board' : board,\
            'number': number,\
            }))

    return HttpResponse(html)

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
    documents  = corpus.get_children()
    number = len(documents)

    sources = query_to_dicts('''select count(*), source 
                        from node_node as t1
                        INNER JOIN documents_document_corpus as t2
                        ON (  t1.id = t2.document_id )
                        WHERE ( t1.user_id = %d AND t2.corpus_id = %d )
                        GROUP BY source
                        order by 1 DESC limit %d;''' % (request.user.pk, int(corpus_id), int(15)))

    sources_donut = []
    for s in sources:
        ss = dict()
        ss['count'] = s['count']
        try:
            ss['part'] = round(ss['count'] * 100 / number)
        except:
            ss['part'] = None
        ss['source'] = s['source']
        sources_donut.append(ss)
    
    
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

        dates = query_to_dicts('''select to_char(t1.date, '%s'), count(*) 
                                from documents_document as t1
                                INNER JOIN documents_document_corpus as t2
                                ON (  t1.id = t2.document_id )
                                WHERE ( t1.user_id = %d AND t2.corpus_id = %d )
                                group by to_char(t1.date, '%s') 
                                order by 1 DESC;''' %  (date_format, request.user.pk, int(corpus_id), date_format))
    
        
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


from node.admin import CorpusForm

class NameForm(forms.Form):
    your_name = forms.CharField(label='Your name', max_length=100)
    sender = forms.EmailField()
    message = forms.CharField(widget=forms.Textarea)
    fichier = forms.FileField()


def get_name(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = CorpusForm(request.POST, request=request)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            return HttpResponseRedirect('/thanks/')

    # if a GET (or any other method) we'll create a blank form
    else:
        form = CorpusForm(request=request)

    return render(request, 'name.html', {'form': form})

