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
    documents  = Document.objects.filter(user=request.user.pk,corpus=c_id).order_by("-date")
    number = len(documents)

    sources = query_to_dicts('''select count(*), source 
                        from documents_document
                        INNER JOIN documents_corpus AS t2
                        ON  t2.id = %d 
                        group by source
                        order by 1 DESC limit %d;''' % (int(c_id), int(15)))
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

    dates = query_to_dicts('''select to_char(documents_document.date, 'YYYY'), count(*) 
                            from documents_document 
                            INNER JOIN documents_corpus AS t2
                            ON  t2.id = %d 
                            group by to_char(documents_document.date, 'YYYY') 
                            order by 1 DESC;''' %  (int(c_id),))
#
#    dates = query_to_dicts('''select to_char(documents_document.date, 'YYYY-MM'), count(*) 
#                            from documents_document 
#                            INNER JOIN documents_corpus AS t2
#                            ON  t2.id = %d 
#                            group by to_char(documents_document.date, 'YYYY-MM') 
#                            order by 1 DESC;''' %  (int(c_id),))
#

    html = t.render(Context({\
            'user': user,\
            'date': date,\
            'project': project,\
            'corpus' : corpus,\
            'documents': documents,\
            'number' : number,\
            'sources_donut' : sources_donut,\
            'dates' : dates,\
            }))
    
    return HttpResponse(html)


