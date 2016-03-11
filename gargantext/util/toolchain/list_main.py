from gargantext.models     import Node, NodeNgram, NodeNodeNgram
from gargantext.util.db    import session
from gargantext.util.lists import UnweightedList
from sqlalchemy            import desc
from gargantext.constants  import DEFAULT_TFIDF_CUTOFF_RATIO, DEFAULT_TFIDF_HARD_LIMIT
from math                  import floor

def do_mainlist(corpus, tfidf_id=None, stoplist_id=None,
                    hard_limit=DEFAULT_TFIDF_HARD_LIMIT,
                    ratio_limit=DEFAULT_TFIDF_CUTOFF_RATIO
                    ):
    """
    Select terms for the mainlist according to a global tfidf and stoplist.

    The number of selected terms will be:
        min(hard_limit, number_of_terms * ratio_limit)

    NB : We use a global tfidf node where the values are global but the ngrams
         are already selected (== only within this corpus documents).

    Parameters:
        2 limits are useful to set a maximum amount of picked terms
        - ratio_limit: relative to the number of distinct ngrams  [0,1]
        - hard_limit: absolute value [default: 1000]
    """

    # retrieve helper nodes if not provided
    if not tfidf_id:
        tfidf_id  = session.query(Node.id).filter(
                                Node.typename  == "TFIDF-GLOBAL",
                                Node.parent_id == corpus.id
                    ).first()
        if not tfidf_id:
            raise ValueError("MAINLIST: TFIDF node needed for mainlist creation")

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
        .filter(NodeNodeNgram.node1_id == tfidf_id)
        .filter(~ NodeNodeNgram.ngram_id.in_(stopterms_subquery))
        .order_by(desc(NodeNodeNgram.score))
        )

    # total count
    nb_ngrams = ordered_filtered_tfidf.count()

    # apply ratio to find smallest limit
    our_limit = min(hard_limit, floor(nb_ngrams * ratio_limit))

    # DB retrieve up to limit => MAINLIST
    top_ngrams_ids = ordered_filtered_tfidf.limit(our_limit).all()

    # now create the new MAINLIST node
    mainlist = corpus.add_child(
        typename  = "MAINLIST",
        name = "Mainlist (in:%s)" % corpus.name[0:10]
    )
    session.add(mainlist)
    session.commit()

    the_id = mainlist.id

    # create UnweightedList object and save (=> new NodeNgram rows)
    UnweightedList(top_ngrams_ids).save(the_id)

    return the_id
