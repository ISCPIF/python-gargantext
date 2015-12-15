from admin.env import *
import sys
from ngram.tfidf import compute_tfidf, compute_tfidf_global
from ngram.cvalue import compute_cvalue
from ngram.specificity import compute_specificity
from ngram.stop import compute_stop
from ngram.group import compute_groups
from gargantext_web.db import get_or_create_node
from ngram.mapList import compute_mapList

from gargantext_web.db import NodeNgram
from admin.utils import WorkflowTracking
from ngram.importExport import exportNgramList, importNgramList
from analysis.periods import phylo_clusters

from ngram.occurrences import compute_occs

from analysis.periods import get_partitions

def ngram_workflow(corpus, n=5000):
    '''
    All the workflow to filter the ngrams.
    '''
    update_state = WorkflowTracking()

#    update_state.processing_(corpus, "Stop words")
#    compute_stop(corpus)
#    
#    update_state.processing_(corpus, "TF-IDF global score")
#    compute_tfidf_global(corpus)
#    
#    part = round(n * 0.9)
#
##    compute_cvalue(corpus,limit=1000) # size
#    
##    part = round(part * 0.8)
#    #print('spec part:', part)
#
#    update_state.processing_(corpus, "Specificity score")
#    compute_specificity(corpus,limit=part)
#    
#    part = round(part * 0.8)
#
#    limit_inf = round(part * 1)
#    limit_sup = round(part * 5)
#    #print(limit_inf,limit_sup)
#    update_state.processing_(corpus, "Synonyms")
#    compute_groups(corpus,limit_inf=limit_inf, limit_sup=limit_sup)
#    
#    update_state.processing_(corpus, "Map list terms")
#    compute_mapList(corpus,limit=1000) # size
#    
#    update_state.processing_(corpus, "TF-IDF local score")
#    compute_tfidf(corpus)
    # update_state.processing_(corpus, "OCCS local score")
    compute_occs(corpus)
    #update_state.processing_(corpus, "0")

if __name__ == "__main__":
    node_id = sys.argv[1] 
    corpus=session.query(Node).filter(Node.id==node_id).first()
    
    ngram_workflow(corpus)
    
    #exportNgramList(corpus, "list.csv")
    #importNgramList(corpus, "list.csv")

    #phylo_clusters(corpus, range(2012,2016))
    get_partitions(corpus)
    #ngram_workflow(corpus)

