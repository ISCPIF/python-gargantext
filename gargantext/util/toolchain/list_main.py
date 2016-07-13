from gargantext.models     import Node, NodeNgram, NodeNodeNgram
from gargantext.util.db    import session
from gargantext.util.lists import UnweightedList
from sqlalchemy            import desc
from gargantext.constants  import DEFAULT_RANK_CUTOFF_RATIO, \
                                  DEFAULT_RANK_HARD_LIMIT

def do_mainlist(corpus,
                    overwrite_id  = None,
                    ranking_scores_id=None, stoplist_id=None,
                    hard_limit=DEFAULT_RANK_HARD_LIMIT,
                    ratio_limit=DEFAULT_RANK_CUTOFF_RATIO
                    ):
    """
    Select top n terms according to a global tfidf ranking and stoplist filter.

    The number of selected terms will be:
        min(hard_limit, number_of_terms * ratio_limit)

    NB : We use a global tfidf node where the values are global but the ngrams
         are already selected (termset_scope == only within this corpus docs).
         TO DISCUSS: allow influence of the local tfidf scores too

    Parameters:
        - the corpus itself
        - a tfidf score for ranking the ngrams
        - a stoplist for filtering some ngrams
        - overwrite_id: optional id of a pre-existing MAINLIST node for this corpus
                     (the Node and its previous NodeNgram rows will be replaced)

      + 2 limits to set the amount of picked terms:
        - ratio_limit ∈ [0,1]: a ratio relative to the number of distinct ngrams
          (default: 0.55)
        - hard_limit: an absolute max value
          (default: 1000)

    """

    # retrieve helper nodes if not provided
    if not ranking_scores_id:
        ranking_scores_id  = session.query(Node.id).filter(
                                Node.typename  == "TIRANK-GLOBAL",
                                Node.parent_id == corpus.id
                    ).first()
        if not ranking_scores_id:
            raise ValueError("MAINLIST: TIRANK node needed for mainlist creation")

    if not stoplist_id:
        stoplist_id  = session.query(Node.id).filter(
                                Node.typename  == "STOPLIST",
                                Node.parent_id == corpus.id
                        ).first()
        if not stoplist_id:
            raise ValueError("MAINLIST: STOPLIST node needed for mainlist creation")

    # the ngrams we don't want
    # NOTE: keep sure we do this only once during the ngram initial workflow
    stopterms_subquery = (session
                            .query(NodeNgram.ngram_id)
                            .filter(NodeNgram.node_id == stoplist_id)
                            .subquery()
                         )

    # tfidf-ranked query
    ordered_filtered_tfidf = (session
        .query(NodeNodeNgram.ngram_id)
        .filter(NodeNodeNgram.node1_id == ranking_scores_id)
        # NOT IN but speed theoretically ok here
        # see http://sqlperformance.com/2012/12/t-sql-queries/left-anti-semi-join
        # but http://stackoverflow.com/questions/2246772/whats-the-difference-between-not-exists-vs-not-in-vs-left-join-where-is-null/2246793#2246793
        .filter(~ NodeNodeNgram.ngram_id.in_(stopterms_subquery))
        .order_by(desc(NodeNodeNgram.score))
        )

    # total count
    nb_ngrams = ordered_filtered_tfidf.count()

    # apply ratio to find smallest limit
    our_limit = min(hard_limit, round(nb_ngrams * ratio_limit))

    print("MAINLIST: keeping %i ngrams out of %i" % (our_limit,nb_ngrams))

    # DB retrieve up to limit => MAINLIST
    top_ngrams_ids = ordered_filtered_tfidf.limit(our_limit).all()

    if overwrite_id:
        # overwrite pre-existing id
        the_id = overwrite_id
        # mainlist = cache.Node[overwrite_id]
    else:
        # now create the new MAINLIST node
        mainlist = corpus.add_child(
            typename  = "MAINLIST",
            name = "Mainlist (in:%s)" % corpus.id
        )
        session.add(mainlist)
        session.commit()
        the_id = mainlist.id

    # create UnweightedList object and save (=> new NodeNgram rows)
    UnweightedList(top_ngrams_ids).save(the_id)

    return the_id
