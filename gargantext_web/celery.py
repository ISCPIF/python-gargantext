# -*- coding: utf-8 -*-

from celery import shared_task
from node import models
from django.db import transaction
from admin.utils import DebugTime, PrintException

import cProfile
#@app.task(bind=True)
@shared_task
def debug_task(request):
    print('Request: {0!r}'.format(request))

from gargantext_web.db import get_session, cache, Node
from ngram.workflow import ngram_workflow


from parsing.corpustools import  parse_resources, extract_ngrams #add_resource,
#from ngram.lists import ngrams2miam

from admin.utils import WorkflowTracking

@shared_task
def apply_workflow(corpus_id):

    dbg = DebugTime('Corpus #%d - WORKFLOW TIMER' % corpus_id)
    dbg.show('ALL WORKFLOW')
    
    update_state = WorkflowTracking()
    
    try :
        mysession = get_session()
        corpus = mysession.query(Node).filter(Node.id==corpus_id).first()

        update_state.processing_(int(corpus_id), "Parsing")
        #cProfile.runctx('parse_resources(corpus)', global,locals)
        parse_resources(corpus, mysession=mysession)

        update_state.processing_(int(corpus_id), "Terms extraction")
        extract_ngrams(corpus, ['title', 'abstract'], nlp=True, mysession=mysession)

        # update_state.processing_(corpus, "")
        ngram_workflow(corpus, mysession=mysession)

        #ngrams2miam(user_id=corpus.user_id, corpus_id=corpus_id)

        print("End of the Workflow for corpus %d" % (corpus_id))
        update_state.processing_(int(corpus_id), "0")
        
        #mysession.close()
        #get_session.remove()
        mysession.remove()
    except Exception as error:
        print(error)
        PrintException()
        #mysession.close()
        #get_session.remove()
        mysession.remove()

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

