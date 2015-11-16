from admin.env import *
from ngram.tfidf import compute_tfidf, compute_tfidf_global
from ngram.cvalue import compute_cvalue
from ngram.specificity import compute_specificity
from ngram.stop import compute_stop
from ngram.group import compute_groups
from gargantext_web.db import get_or_create_node
from ngram.mapList import compute_mapList

from gargantext_web.db import NodeNgram
#from gargantext_web.celery import update_processing


def ngram_workflow(corpus, n=5000):
    '''
    All the workflow to filter the ngrams.
    '''
    
    compute_stop(corpus)
    
    compute_tfidf_global(corpus)
    
    part = round(n * 0.9)

    compute_cvalue(corpus,limit=1000) # size
    
    part = round(part * 0.8)
    print('spec part:', part)

    compute_specificity(corpus,limit=part)
    
    part = round(part * 0.8)

    limit_inf = round(part * 1)
    limit_sup = round(part * 5)
    print(limit_inf,limit_sup)
    compute_groups(corpus,limit_inf=limit_inf, limit_sup=limit_sup)
    
    compute_mapList(corpus,limit=1000) # size
    
    compute_tfidf(corpus)
    

node_id = 1427298
#corpus=session.query(Node).filter(Node.id==540420).first()
corpus=session.query(Node).filter(Node.id==node_id).first()
ngram_workflow(corpus)


#update_processing(corpus, 0)

check_stop = False

if check_stop:
    stop = get_or_create_node(corpus=corpus,nodetype='StopList')
#session.query(NodeNgram).filter(NodeNgram.node_id==stop.id).delete()
#session.commit()
    stop_ngrams = (session.query(Ngram)
                          .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                          .filter(NodeNgram.node_id==stop.id)
                          .all()
                    )

    print([n for n in stop_ngrams])
