#from admin.env import *
from ngram.tfidf import compute_tfidf, compute_tfidf_global
from ngram.cvalue import compute_cvalue
from ngram.specificity import compute_specificity
from ngram.stop import compute_stop
from ngram.group import compute_groups
from gargantext_web.db import get_or_create_node
from ngram.mapList import compute_mapList
# from ngram.occurrences import compute_occs

from gargantext_web.db import session , Node , NodeNgram
from admin.utils import WorkflowTracking


def ngram_workflow(corpus, n=5000):
    '''
    All the workflow to filter the ngrams.
    '''
    update_state = WorkflowTracking()

    update_state.processing_(corpus, "Stop words")
    compute_stop(corpus)
    
    update_state.processing_(corpus, "TF-IDF global score")
    compute_tfidf_global(corpus)
    
    part = round(n * 0.9)

#    compute_cvalue(corpus,limit=1000) # size
    
#    part = round(part * 0.8)
    #print('spec part:', part)

    update_state.processing_(corpus, "Specificity score")
    compute_specificity(corpus,limit=part)
    
    part = round(part * 0.8)

    limit_inf = round(part * 1)
    limit_sup = round(part * 5)
    #print(limit_inf,limit_sup)
    update_state.processing_(corpus, "Synonyms")
    compute_groups(corpus,limit_inf=limit_inf, limit_sup=limit_sup)
    
    update_state.processing_(corpus, "Map list terms")
    compute_mapList(corpus,limit=1000) # size
    
    update_state.processing_(corpus, "TF-IDF local score")
    compute_tfidf(corpus)
    # update_state.processing_(corpus, "OCCS local score")
    # compute_occs(corpus)

#corpus=session.query(Node).filter(Node.id==540420).first()
#corpus=session.query(Node).filter(Node.id==559637).first()



#update_stateprocessing(corpus, 0)

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
