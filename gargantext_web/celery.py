# -*- coding: utf-8 -*-

from celery import shared_task
from node import models
from django.db import transaction

import cProfile
#@app.task(bind=True)
@shared_task
def debug_task(request):
    print('Request: {0!r}'.format(request))

from gargantext_web.db import session, cache, Node
from ngram.workflow import ngram_workflow


@shared_task
def apply_sum(x, y):
    print(x+y)
    print(session.query(Node.name).first())


from parsing.corpustools import  parse_resources, extract_ngrams #add_resource,
from ngram.lists import ngrams2miam

from admin.utils import WorkflowTracking

@shared_task
def apply_workflow(corpus_id):

    update_state = WorkflowTracking()

    corpus = session.query(Node).filter(Node.id==corpus_id).first()

    update_state.processing_(corpus, "Parsing")
    #cProfile.runctx('parse_resources(corpus)', global,locals)
    parse_resources(corpus)

    update_state.processing_(corpus, "Terms extraction")
    extract_ngrams(corpus, ['title', 'abstract'], nlp=True)

    # update_state.processing_(corpus, "")
    ngram_workflow(corpus)

    #ngrams2miam(user_id=corpus.user_id, corpus_id=corpus_id)
    update_state.processing_(corpus, "0")

    print("End of the Workflow for corpus %d" % (corpus_id))


@shared_task
def empty_trash(corpus_id):
    nodes = models.Node.objects.filter(type_id=cache.NodeType['Trash'].id).all()
    with transaction.atomic():
        for node in nodes:
            try:
                node.children.delete()
            except Exception as error:
                print(error)

            node.delete()
    print("Nodes deleted")

