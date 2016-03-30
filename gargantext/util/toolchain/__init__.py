from .parsing             import parse
from .ngrams_extraction   import extract_ngrams
from .hyperdata_indexing  import index_hyperdata

# in usual run order
from .list_stop           import do_stoplist
from .metric_tfidf        import compute_occs, compute_tfidf_local, compute_cumulated_tfidf
from .list_main           import do_mainlist
from .ngram_coocs         import compute_coocs
from .metric_specificity  import compute_specificity
from .list_map            import do_maplist     # TEST
from .ngram_groups        import compute_groups

from gargantext.util.db   import session
from gargantext.models    import Node

from datetime             import datetime
from celery               import shared_task

@shared_task
def parse_extract(corpus):
    # retrieve corpus from database from id
    if isinstance(corpus, int):
        corpus_id = corpus
        corpus = session.query(Node).filter(Node.id == corpus_id).first()
        if corpus is None:
            print('NO SUCH CORPUS: #%d' % corpus_id)
            return
    # apply actions
    print('CORPUS #%d' % (corpus.id))
    parse(corpus)

    # was there an error in the process ?
    if corpus.status()['error']:
        print("ERROR: aborting parse_extract for corpus #%i" % corpus_id)
        return None

    print('CORPUS #%d: parsed' % (corpus.id))
    extract_ngrams(corpus)
    print('CORPUS #%d: extracted ngrams' % (corpus.id))

@shared_task
def parse_extract_indexhyperdata(corpus):
    # retrieve corpus from database from id
    if isinstance(corpus, int):
        corpus_id = corpus
        corpus = session.query(Node).filter(Node.id == corpus_id).first()
        if corpus is None:
            print('NO SUCH CORPUS: #%d' % corpus_id)
            return
    # apply actions
    print('CORPUS #%d' % (corpus.id))
    parse(corpus)
    print('CORPUS #%d: parsed' % (corpus.id))
    extract_ngrams(corpus)
    print('CORPUS #%d: extracted ngrams' % (corpus.id))
    index_hyperdata(corpus)
    print('CORPUS #%d: indexed hyperdata' % (corpus.id))
    
    # -------------------------------
    # temporary ngram lists workflow
    # -------------------------------
    print('CORPUS #%d: [%s] starting ngram lists computation' % (corpus.id, t()))

    # -> stoplist: filter + write (to Node and NodeNgram)
    stop_id = do_stoplist(corpus)
    print('CORPUS #%d: [%s] new stoplist node #%i' % (corpus.id, t(), stop_id))

    # -> write groups to Node and NodeNgramNgram
    group_id = compute_groups(corpus, stoplist_id = None)
    print('CORPUS #%d: [%s] new grouplist node #%i' % (corpus.id, t(), group_id))

    # -> write occurrences to Node and NodeNodeNgram # possible: factorize with tfidf
    occ_id = compute_occs(corpus)
    print('CORPUS #%d: [%s] new occs node #%i' % (corpus.id, t(), occ_id))

    # ------------
    # -> write local tfidf similarities to Node and NodeNodeNgram
    ltfidf_id = compute_tfidf_local(corpus)
    print('CORPUS #%d: [%s] new localtfidf node #%i' % (corpus.id, t(), ltfidf_id))

    # -> write global and cumulated tfidf to Node and NodeNodeNgram
    gtfidf_id = compute_cumulated_tfidf(corpus, scope="global")
    print('CORPUS #%d: [%s] new globaltfidf node #%i' % (corpus.id, t(), gtfidf_id))

    # -> mainlist: filter + write (to Node and NodeNgram)
    mainlist_id = do_mainlist(corpus,
                              tfidf_id = gtfidf_id,
                              stoplist_id = stop_id)
    print('CORPUS #%d: [%s] new mainlist node #%i' % (corpus.id, t(), mainlist_id))

    # ------------
    # -> cooccurrences: compute + write (=> Node and NodeNodeNgram)
    cooc_id = compute_coocs(corpus, mainlist_id = mainlist_id)
    print('CORPUS #%d: [%s] new coocs node #%i' % (corpus.id, t(), cooc_id))

    # -> specificity: compute + write (=> NodeNodeNgram)
    spec_id = compute_specificity(corpus, cooc_id=cooc_id)
    print('CORPUS #%d: [%s] new specificity node #%i' % (corpus.id, t(), spec_id))

    # ?? maplist: compute + write (to Node and NodeNgram)
    map_id = do_maplist(corpus,
                        mainlist_id = mainlist_id,
                        specificity_id=spec_id,
                        grouplist_id=group_id)
    print('CORPUS #%d: [%s] new maplist node #%i' % (corpus.id, t(), map_id))

    print('CORPUS #%d: [%s] FINISHED ngram lists computation' % (corpus.id, t()))


def t():
    return datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
