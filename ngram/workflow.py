#from admin.env import *
from ngram.tfidf import compute_tfidf, compute_tfidf_global
from ngram.cvalue import compute_cvalue
from ngram.specificity import compute_specificity
from ngram.stop import compute_stop
from ngram.group import compute_groups
from gargantext_web.db import get_or_create_node
from ngram.mapList import compute_mapList
from ngram.occurrences import compute_occs

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
    try:
        compute_groups(corpus,limit_inf=limit_inf, limit_sup=limit_sup)
    except Exception as error:
        print("Workflow Ngram Group error", error)
        pass
    
    update_state.processing_(corpus, "Map list terms")
    compute_mapList(corpus,limit=1000) # size
    
    update_state.processing_(corpus, "TF-IDF local score")
    compute_tfidf(corpus)

    update_state.processing_(corpus, "Occurrences")
    compute_occs(corpus)


