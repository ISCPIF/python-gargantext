
from gargantext.settings  import DEBUG
from .parsing             import parse
from .ngrams_extraction   import extract_ngrams
from .hyperdata_indexing  import index_hyperdata

# in usual run order
from .list_stop           import do_stoplist
from .ngram_groups        import compute_groups
from .metric_tfidf        import compute_occs, compute_tfidf_local, compute_ti_ranking
from .list_main           import do_mainlist
#from .ngram_coocs         import compute_coocs
from .ngram_coocs_old_sqlalchemy_version import compute_coocs
from .metric_specgen      import compute_specgen
from .list_map            import do_maplist
from .mail_notification   import notify_owner
from gargantext.util.db   import session
from gargantext.models    import Node

from datetime             import datetime
from celery               import shared_task

#@shared_task
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
    docs_count = corpus.children("DOCUMENT").count()
    print('CORPUS #%d: parsed %d documents' % (corpus.id, docs_count))
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
    # Instantiate status
    corpus.status('Workflow', progress=1)
    corpus.save_hyperdata()
    session.commit()
    # FIXME: 'Workflow' will still be uncomplete when 'Index' and 'Lists' will
    #        get stacked into hyperdata['statuses'], but doing corpus.status()
    #        will return only the 1st uncomplete action (corpus.status() doesn't
    #        understand "subactions")

    # apply actions
    print('CORPUS #%d' % (corpus.id))
    
    corpus.status('Docs', progress=1)
    corpus.save_hyperdata()
    session.commit()
    parse(corpus)
    
    docs = corpus.children("DOCUMENT").count()
    print('CORPUS #%d: parsed %d' % (corpus.id, docs))
    extract_ngrams(corpus)

    # Preparing Databse
    # Indexing
    #

    corpus.status('Index', progress=0)
    corpus.save_hyperdata()
    session.commit()


    print('CORPUS #%d: extracted ngrams' % (corpus.id))
    index_hyperdata(corpus)
    print('CORPUS #%d: indexed hyperdata' % (corpus.id))

    # -> 'favorites' node
    favs = corpus.add_child(
            typename='FAVORITES', name='favorite docs in "%s"' % corpus.name
            )

    session.add(favs)
    session.commit()
    print('CORPUS #%d: [%s] new favorites node #%i' % (corpus.id, t(), favs.id))


    corpus.status('Index', progress=1, complete=True)
    corpus.save_hyperdata()
    session.commit()


    # -------------------------------
    # temporary ngram lists workflow
    # -------------------------------

    corpus.status('Lists', progress=0)
    corpus.save_hyperdata()
    session.commit()


    print('CORPUS #%d: [%s] starting ngram lists computation' % (corpus.id, t()))

    # -> stoplist: filter + write (to Node and NodeNgram)
    stop_id = do_stoplist(corpus)
    print('CORPUS #%d: [%s] new stoplist node #%i' % (corpus.id, t(), stop_id))

    # -> write groups to Node and NodeNgramNgram
    group_id = compute_groups(corpus, stoplist_id = None)
    print('CORPUS #%d: [%s] new grouplist node #%i' % (corpus.id, t(), group_id))

    # ------------
    # -> write occurrences to Node and NodeNodeNgram
    occ_id = compute_occs(corpus, groupings_id = group_id)
    print('CORPUS #%d: [%s] new occs node #%i' % (corpus.id, t(), occ_id))

    # -> write cumulated ti_ranking (tfidf ranking vector) to Node and NodeNodeNgram
    tirank_id = compute_ti_ranking(corpus,
                                   groupings_id = group_id,
                                   count_scope="global")
    print('CORPUS #%d: [%s] new ti ranking node #%i' % (corpus.id, t(), tirank_id))

    # -> mainlist: filter + write (to Node and NodeNgram)
    mainlist_id = do_mainlist(corpus,
                              ranking_scores_id = tirank_id,
                              stoplist_id = stop_id)
    print('CORPUS #%d: [%s] new mainlist node #%i' % (corpus.id, t(), mainlist_id))

    # -> write local tfidf similarities to Node and NodeNodeNgram
    ltfidf_id = compute_tfidf_local(corpus,
                                    on_list_id=mainlist_id,
                                    groupings_id = group_id)
    print('CORPUS #%d: [%s] new localtfidf node #%i' % (corpus.id, t(), ltfidf_id))
    # => used for doc <=> ngram association

    # ------------
    # -> cooccurrences on mainlist: compute + write (=> Node and NodeNgramNgram)*
    coocs = compute_coocs(corpus,
                            on_list_id = mainlist_id,
                            groupings_id = group_id,
                            just_pass_result = True,
                           # symmetry_filter  = True,
                            diagonal_filter = False) # preserving the diagonal
                                                     # (useful for spec/gen)
    print('CORPUS #%d: [%s] computed mainlist coocs for specif rank' % (corpus.id, t()))

    # -> specclusion/genclusion: compute + write (2 Nodes + 2 lists in NodeNgram)
    (spec_id, gen_id) = compute_specgen(corpus,cooc_matrix = coocs)
    # no need here for subforms because cooc already counted them in mainform
    print('CORPUS #%d: [%s] new spec-clusion node #%i' % (corpus.id, t(), spec_id))
    print('CORPUS #%d: [%s] new gen-clusion node #%i' % (corpus.id, t(), gen_id))

    # maplist: compute + write (to Node and NodeNgram)
    map_id = do_maplist(corpus,
                        mainlist_id = mainlist_id,
                        specclusion_id=spec_id,
                        genclusion_id=gen_id,
                        grouplist_id=group_id
                        )
    print('CORPUS #%d: [%s] new maplist node #%i' % (corpus.id, t(), map_id))

    print('CORPUS #%d: [%s] FINISHED ngram lists computation' % (corpus.id, t()))

    corpus.status('Lists', progress=0, complete=True)
    corpus.save_hyperdata()
    session.commit()


    if DEBUG is False:
        print('CORPUS #%d: [%s] FINISHED Sending email notification' % (corpus.id, t()))
        notify_owner(corpus)

    corpus.status('Workflow', progress=10, complete=True)
    corpus.save_hyperdata()
    session.commit()

@shared_task
def recount(corpus):
    """
    Recount essential metrics of the toolchain after group modifications.

    ==> updates all scores in terms table
    ==> updates tfidf relationship b/w term and doc

    When groups change, the metrics need to be updated because subforms must be
    added to their new mainform aggregate values:
         - occurrences
         - ndocs
         - ti_rank
         - coocs
         - specclusion/genclusion
         - tfidf

    NB: no new extraction, no list change, just the metrics
    """
    # 1) we'll need the new groups and mainlist as basis
    group_id = corpus.children("GROUPLIST").first().id
    mainlist_id = corpus.children("MAINLIST").first().id

    # 2) and we're going to overwrite the previous metric nodes
    try:
        old_occ_id    = corpus.children("OCCURRENCES").first().id
    except:
        old_occ_id    = None

    try:
        old_tirank_id = corpus.children("TIRANK-GLOBAL").first().id
    except:
        old_tirank_id = None

    try:
        old_spec_id   = corpus.children("SPECCLUSION").first().id
    except:
        old_spec_id   = None

    try:
        old_gen_id   = corpus.children("GENCLUSION").first().id
    except:
        old_gen_id   = None

    try:
        old_ltfidf_id = corpus.children("TFIDF-CORPUS").first().id
    except:
        old_ltfidf_id = None

    # 3) we redo the required toolchain parts
    # -------------------------------------------

    # Instantiate status
    corpus.status('Recounting mini-workflow', progress=1)
    corpus.save_hyperdata()
    session.commit()

    # -> overwrite occurrences (=> NodeNodeNgram)
    occ_id = compute_occs(corpus,
                            groupings_id = group_id,
                            overwrite_id=old_occ_id)
    print('RECOUNT #%d: [%s] updated occs node #%i' % (corpus.id, t(), occ_id))

    # -> write cumulated ti_ranking (tfidf ranking vector) (=> NodeNodeNgram)
    tirank_id = compute_ti_ranking(corpus,
                                   groupings_id = group_id,
                                   count_scope="global",
                                   overwrite_id=old_tirank_id)
    print('RECOUNT #%d: [%s] updated ti ranking node #%i' % (corpus.id, t(), tirank_id))

    # -> write local tfidf similarities to (=> NodeNodeNgram)
    ltfidf_id = compute_tfidf_local(corpus,
                                    on_list_id = mainlist_id,
                                    groupings_id = group_id,
                                    overwrite_id = old_ltfidf_id)
    print('RECOUNT #%d: [%s] updated localtfidf node #%i' % (corpus.id, t(), ltfidf_id))
    # => used for doc <=> ngram association

    # ------------
    # -> cooccurrences on mainlist: compute + write (=> NodeNgramNgram)
    coocs = compute_coocs(corpus,
                            on_list_id = mainlist_id,
                            groupings_id = group_id,
                            just_pass_result = True)
    print('RECOUNT #%d: [%s] updated mainlist coocs for specif rank' % (corpus.id, t()))


    # -> specclusion/genclusion: compute + write (=> NodeNodeNgram)
    (spec_id, gen_id) = compute_specgen(corpus, cooc_matrix = coocs,
                                        spec_overwrite_id = old_spec_id,
                                        gen_overwrite_id = old_gen_id)

    print('RECOUNT #%d: [%s] updated spec-clusion node #%i' % (corpus.id, t(), spec_id))
    print('RECOUNT #%d: [%s] updated gen-clusion node #%i' % (corpus.id, t(), gen_id))

    print('RECOUNT #%d: [%s] FINISHED metric recounts' % (corpus.id, t()))

    corpus.status('Recounting mini-workflow', progress=10, complete=True)
    corpus.save_hyperdata()
    session.commit()

def t():
    return datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
