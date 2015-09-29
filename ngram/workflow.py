#from admin.env import *
from ngram.tfidf import compute_tfidf, compute_tfidf_global
from ngram.cvalue import compute_cvalue
from ngram.specificity import compute_specificity
#from ngram.stop import compute_stop
from ngram.group import compute_groups
from ngram.miam import compute_miam
from gargantext_web.db import get_or_create_node

def ngram_workflow(corpus):
    '''
    All the workflow to filter the ngrams.
    '''
    compute_tfidf(corpus)
    compute_tfidf_global(corpus)
    compute_cvalue(corpus,limit=3000) # size
    compute_specificity(corpus,limit=200)
#    compute_stop(corpus)
    compute_groups(corpus,limit_inf=400, limit_sup=600)
#    compute_miam(corpus,limit=100) # size

#corpus=session.query(Node).filter(Node.id==244250).first()
#ngram_workflow(corpus)

#cvalue = get_or_create_node(corpus=corpus,nodetype='Cvalue')
#print(session.query(NodeNodeNgram).filter(NodeNodeNgram.nodex_id==cvalue.id).count())

