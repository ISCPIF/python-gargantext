# -*- coding: utf-8 -*-

from celery import shared_task
from node import models

#@app.task(bind=True)
@shared_task
def debug_task(request):
    print('Request: {0!r}'.format(request))

from gargantext_web.db import session, Node

@shared_task
def apply_sum(x, y):
    print(x+y)
    print(session.query(Node.name).first())


from parsing.corpustools import add_resource, parse_resources, extract_ngrams, compute_tfidf

from admin.utils import PrintException

def update_processing(corpus, step=0):
    try:
        corpus.hyperdata.update({'Processing' : step})
        session.query(Node).filter(Node.id==corpus.id).update({'hyperdata' : corpus.hyperdata})
        session.commit()
    except :
        PrintException()

@shared_task
def apply_workflow(corpus_id):
    corpus = session.query(Node).filter(Node.id==corpus_id).first()

    update_processing(corpus, 1)
    parse_resources(corpus)
    
    update_processing(corpus, 2)
    extract_ngrams(corpus, ['title', 'abstract'])
    
    update_processing(corpus, 3)
    compute_tfidf(corpus)
    
    update_processing(corpus, 0)



