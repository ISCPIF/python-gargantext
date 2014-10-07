from django.shortcuts import redirect
from django.shortcuts import render

from django.http import Http404, HttpResponse
from django.template.loader import get_template
from django.template import Context

from documents.models import Project, Corpus, Document

from django.contrib.auth.models import User

import datetime
from itertools import *
from django.db import connection

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

    elif format == "years":
        form = "%Y"
    
    elif format == "months":
        form = "%Y-%m"
    elif format == "days":
        form = "%Y-%m-%d"

    start_dt = datetime.datetime.strptime(start_dt, form)
    if end_dt: end_dt = datetime.datetime.strptime(end_dt, form)
    while start_dt <= end_dt:
        yield start_dt.strftime(form)
        start_dt += datetime.timedelta(days=1)

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
    projects = Project.objects.all().filter(user=request.user.pk).order_by("-date")
    number = len(projects)

    html = t.render(Context({\
            'user': user,\
            'date': date,\
            'projects': projects,\
            'number': number,\
            }))
    
    return HttpResponse(html)

def project(request, p_id):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)
    
    try:
        offset = str(p_id)
    except ValueError:
        raise Http404()

    t = get_template('project.html')
    user = request.user

    date = datetime.datetime.now()
    project = Project.objects.get(pk=p_id)
    corpora = Corpus.objects.all().filter(project_id=p_id,user=request.user.pk)
    number = len(corpora)
    
    html = t.render(Context({\
            'user': user,\
            'date': date,\
            'project': project,\
            'corpora' : corpora,\
            'number': number,\
            }))
    
    return HttpResponse(html)

def corpus(request, p_id, c_id):
    if not request.user.is_authenticated():
        return redirect('/login/?next=%s' % request.path)
    
    try:
        offset = str(p_id)
    except ValueError:
        raise Http404()

    t = get_template('corpus.html')
    user = request.user

    date = datetime.datetime.now()
    
    project = Project.objects.get(pk=p_id, user=request.user.pk)
    corpus  = Corpus.objects.get(pk=c_id, user=request.user.pk)
    print(Document.objects.filter(corpus=c_id, user=request.user.pk).query)
    documents  = Document.objects.filter(user=request.user.pk,corpus=c_id).order_by("-date")
    number = len(documents)

    sources = query_to_dicts('''select count(*), source 
                        from documents_document as t1
                        INNER JOIN documents_document_corpus as t2
                        ON (  t1.id = t2.document_id )
                        WHERE ( t1.user_id = %d AND t2.corpus_id = %d )
                        GROUP BY source
                        order by 1 DESC limit %d;''' % (request.user.pk, int(c_id), int(15)))

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
        elif duree.days > 60:
            date_format = 'YYYY-MM'
        else:
            date_format = 'YYYY-MM-DD'

        dates = query_to_dicts('''select to_char(t1.date, '%s'), count(*) 
                                from documents_document as t1
                                INNER JOIN documents_document_corpus as t2
                                ON (  t1.id = t2.document_id )
                                WHERE ( t1.user_id = %d AND t2.corpus_id = %d )
                                group by to_char(t1.date, '%s') 
                                order by 1 DESC;''' %  (date_format, request.user.pk, int(c_id), date_format))
    except:
        dates = None
    histo = []

    for e in date_range('1990-01-01', '1992-02-01', format='days'):
        print(e)
#        if date_format = 'YYYY':
#            while True:
#                if d -histo.append(d)
    for d in dates:
        histo.append(d)

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


