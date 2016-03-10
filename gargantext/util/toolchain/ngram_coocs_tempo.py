from gargantext.models     import Node, NodeNgram, NodeNgramNgram
from gargantext.util.lists import WeightedMatrix
from gargantext.util.db    import session, aliased, func
from gargantext.constants  import DEFAULT_COOC_THRESHOLD

def compute_coocs(corpus,
                    threshold = DEFAULT_COOC_THRESHOLD,
                    weighted  = False,
                    our_id    = None,
                    stop_id   = None,
                    symmetry_filter = True):
    """
    Count how often some extracted terms appear
    together in a small context (document)
    throughout a larger context (corpus).

    node_id | ngram_id | weight       ngram1_id | ngram2_id | ucooc | wcooc |
    --------+----------+--------      ----------+-----------+-------+-------+
      MYDOC |      487 |      1   =>        487 |       294 |     1 |     4 |
      MYDOC |      294 |      3

    Fill that info in DB:
      - a *new* COOCCURRENCES node
      - and all corresponding NodeNgramNgram rows

    worse case complexity ~ O(N²/2) with N = number of ngrams

    Parameters:
      - threshold: on output ucooc count (previously called hapax)
      - weighted: if False normal cooc to be saved as result
                  if True  weighted cooc (experimental)
      - stop_id: stoplist for filtering input ngrams
      - TODO cvalue_id: allow a metric as input filter
      - TODO n_min, n_max : filter on Ngram.n (aka length of ngram)
      - TODO start, end : filter on document date

     (deprecated parameters)
      - field1,2: allowed to count other things than ngrams (eg tags) but no use case at present
      - isMonopartite: ?? used a nodes_hyperdata_ngrams table ???

    basic idea for one doc
    ======================
    each pair of ngrams sharing same doc (node_id)
        SELEC idx1.ngram_id, idx2.ngram_id
        FROM nodes_ngrams AS idx1, nodes_ngrams AS idx2
        ---------------------------------
        WHERE idx1.node_id = idx2.node_id      <== that's cooc
        ---------------------------------
        AND idx1.ngram_id <> idx2.ngram_id
        AND idx1.node_id = MY_DOC ;

    on entire corpus
    =================
    coocs for each doc :
      - each given pair like (termA, termB) will likely appear several times
        => we do GROUP BY (x1.ngram_id, x2.ngram_id)
      - normally we can count unique appearances of the pair (ucooc)
      - we can count sum of sum of weights in the pair (wcooc or cofreq)

    TODO
    ====
      use WeightedMatrix
    """

    # /!\ big combinatorial complexity /!\
    # pour 8439 lignes dans l'index nodes_ngrams dont 1442 avec occ > 1
    #  1.859.408 lignes pour la requête cooc simple
    #     71.134 lignes en se limitant aux ngrammes qui ont une occ > 1 (weight)

    # docs of our corpus
    docids_subquery = (session
                        .query(Node.id)
                        .filter(Node.parent_id == corpus.id)
                        .filter(Node.typename == "DOCUMENT")
                        .subquery()
                       )

    # 2 x the occurrence index table
    x1 = aliased(NodeNgram)
    x2 = aliased(NodeNgram)

    # cooccurrences columns definition
    ucooc = func.count(x1.ngram_id).label("ucooc")

    # 1) MAIN DB QUERY
    coocs_query = (
        session.query(x1.ngram_id, x2.ngram_id, ucooc)

            .filter(x1.node_id == x2.node_id)      # <- by definition of cooc
            .filter(x1.ngram_id != x2.ngram_id)     # <- b/c not with itself
            .filter(x1.node_id.in_(docids_subquery)) # <- b/c within corpus
            .group_by(x1.ngram_id, x2.ngram_id)
           )

    # 2) INPUT FILTERS (reduce N before O(N²))
    #    £TODO add possibility to restrict to the mainlist
    if stop_id:
        stop_subquery = (
            session.query(NodeNgram.ngram_id)
                .filter(NodeNgram.node_id == stop_id)
                .subquery()
                )

        coocs_query = ( coocs_query
            .filter( ~ x1.ngram_id.in_(stop_subquery) )
            .filter( ~ x2.ngram_id.in_(stop_subquery) )
        )

    if symmetry_filter:
        # 1 filtre tenant en compte de la symétrie
        #  -> réduit le travail de moitié !!
        #  -> mais empêchera l'accès direct aux cooccurrences de x2
        #  -> seront éparpillées: notées dans les x1 qui ont précédé x2
        #  -> récupération sera plus couteuse via des requêtes OR comme:
        #       WHERE ngram1 = mon_ngram OR ngram2 = mon_ngram
        coocs_query = coocs_query.filter(x1.ngram_id  < x2.ngram_id)

    # ------------
    # 2 filtres amont possibles pour réduire combinatoire
    #         - par exemple 929k lignes => 35k lignes
    #         - ici sur weight mais dégrade les résultats
    #            => imaginable sur une autre métrique (cvalue ou tfidf?)
    # coocs_query = coocs_query.filter(x1.weight > 1)
    # coocs_query = coocs_query.filter(x2.weight > 1)
    # ------------


    # 3) OUTPUT FILTERS
    # ------------------
    # threshold
    #
    coocs_query = coocs_query.having(ucooc > threshold)

    # 4) EXECUTE QUERY
    # ----------------
    #  => storage in our matrix structure
    matrix = WeightedMatrix(coocs_query.all())

    # 5) SAVE
    # --------
    if our_id:
        # use pre-existing id
        the_id = our_id
    else:
        # create the new cooc node
        the_cooc = Node(
                        typename  = "COOCCURRENCES",
                        name      = "Coocs (in:%s)" % corpus.name[0:10],
                        parent_id = corpus.id,
                        user_id   = corpus.user_id,

                        # saving the parameters of the analysis in the Node JSON
                        hyperdata = { 'corpus': corpus.id,
                                      'threshold': threshold }
                    )
        session.add(the_cooc)
        session.commit()

        the_id = the_cooc.id

    # ==> save all NodeNgramNgram with link to new cooc node id
    matrix.save(the_id)

    return the_id
