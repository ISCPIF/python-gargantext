#from admin.env import *
from ngram.tfidf import compute_tfidf, compute_tfidf_global
from ngram.cvalue import compute_cvalue
from ngram.specificity import compute_specificity
#from ngram.stop import compute_stop
from ngram.group import compute_groups
from ngram.miam import compute_miam
from gargantext_web.db import get_or_create_node
#from gargantext_web.celery import update_processing


def ngram_workflow(corpus, n=5000):
    '''
    All the workflow to filter the ngrams.
    '''
    compute_tfidf_global(corpus)
    
    part = round(n * 0.8)

    compute_cvalue(corpus,limit=part) # size
    
    part = round(part * 0.4)
    print('spec part:', part)

    compute_specificity(corpus,limit=part)
    
    part = round(part * 0.5)

#    compute_stop(corpus)
    limit_inf = round(part * 1)
    limit_sup = round(part * 5)
    print(limit_inf,limit_sup)
    compute_groups(corpus,limit_inf=limit_inf, limit_sup=limit_sup)
    
#    compute_miam(corpus,limit=part) # size
    
    compute_tfidf(corpus)
    

#corpus=session.query(Node).filter(Node.id==257579).first()
#ngram_workflow(corpus)
#update_processing(corpus, 0)

#cvalue = get_or_create_node(corpus=corpus,nodetype='Cvalue')
#print(session.query(NodeNodeNgram).filter(NodeNodeNgram.nodex_id==cvalue.id).count())

