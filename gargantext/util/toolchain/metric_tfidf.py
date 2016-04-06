"""
Computes ngram scores with 3 ranking functions:
   - the simple sum of occurrences inside the corpus
   - the tfidf inside the corpus
   - the global tfidf for all corpora having same source

FIXME: "having the same source" means we need to select inside hyperdata
       with a (perhaps costly) JSON query: WHERE hyperdata->'resources' @> ...
"""

from gargantext.models   import Node, NodeNgram, NodeNodeNgram
from gargantext.util.db  import session, bulk_insert, func # = sqlalchemy.func like sum() or count()
from sqlalchemy          import text  # for query from raw SQL statement
from math                import log
# £TODO
# from gargantext.util.lists import WeightedContextIndex


def compute_occs(corpus, overwrite_id = None):
    """
    # TODO check if cumulated occs correspond to app's use cases and intention

    Calculates sum of occs per ngram within corpus
    (used as info in the ngrams table view)

    ? optimize ?  OCCS here could be calculated simultaneously within TFIDF-CORPUS loop

    Parameters:
        - overwrite_id: optional id of a pre-existing OCCURRENCES node for this corpus
                     (the Node and its previous NodeNodeNgram rows will be replaced)
    """

    # 1) all the doc_ids of our corpus (scope of counts for filter)
    # slower alternative: [doc.id for doc in corpus.children('DOCUMENT').all()]
    docids_subquery = (session
                        .query(Node.id)
                        .filter(Node.parent_id == corpus.id)
                        .filter(Node.typename == "DOCUMENT")
                        .subquery()
                       )

    # 2) our sums per ngram_id
    occ_sums = (session
                .query(
                    NodeNgram.ngram_id,
                    func.sum(NodeNgram.weight)
                 )
                .filter(NodeNgram.node_id.in_(docids_subquery))
                .group_by(NodeNgram.ngram_id)
                .all()
               )

    # example result = [(1970, 1.0), (2024, 2.0),  (259, 2.0), (302, 1.0), ... ]
    #                    ^^^^  ^^^
    #                ngram_id  sum_wei


    if overwrite_id:
        # overwrite pre-existing id
        the_id = overwrite_id
        # occnode = cache.Node[overwrite_id]
    else:
        # create the new OCCURRENCES node
        occnode = corpus.add_child(
            typename  = "OCCURRENCES",
            name = "occ_sums (in:%s)" % corpus.id
        )
        session.add(occnode)
        session.commit()
        the_id = occnode.id

    # reflect that in NodeNodeNgrams (could be NodeNgram but harmony with tfidf)
    # £TODO replace bulk_insert by something like WeightedContextMatrix.save()
    bulk_insert(
        NodeNodeNgram,
        ('node1_id' , 'node2_id', 'ngram_id', 'score'),
        ((the_id, corpus.id,  res[0], res[1]) for res in occ_sums)
    )

    return the_id


def compute_cumulated_tfidf(corpus, scope="local", overwrite_id=None):
    """
    # TODO check if cumulated tfs correspond to app's use cases and intention

    Calculates tfidf ranking (cumulated tfidf) within the given scope

    Parameters:
      - the corpus itself
      - scope: {"local" or "global"}
      - overwrite_id: optional id of a pre-existing TFIDF-XXXX node for this corpus
                   (the Node and its previous NodeNodeNgram rows will be replaced)
    """

    # local <=> within this corpus
    if scope == "local":
        # All docs of this corpus
        docids_subquery = (session
                            .query(Node.id)
                            .filter(Node.parent_id == corpus.id)
                            .filter(Node.typename == "DOCUMENT")
                            .subquery()
                           )
    # global <=> within all corpora of this source
    elif scope == "global":
        this_source_type = corpus.resources()[0]['type']

        # all corpora with the same source type
        # (we need raw SQL query for postgres JSON operators) (TODO test speed)
        same_source_corpora_query = (session
                            .query(Node.id)
                            .from_statement(text(
                                """
                                SELECT id FROM nodes
                                WHERE hyperdata->'resources' @> '[{\"type\"\:%s}]'
                                """ % this_source_type
                                ))
                            )

        # All docs **in all corpora of the same source**
        docids_subquery = (session
                            .query(Node.id)
                            .filter(Node.parent_id.in_(same_source_corpora_query))
                            .filter(Node.typename == "DOCUMENT")
                            .subquery()
                           )

    # N
    total_docs = session.query(docids_subquery).count()

    # or perhaps at least do the occurrences right now at the same time
    tf_nd = (session
                    .query(
                        NodeNgram.ngram_id,
                        func.sum(NodeNgram.weight),    # tf: same as occnode
                        func.count(NodeNgram.node_id)  # nd: n docs with term
                     )
                    .filter(NodeNgram.node_id.in_(docids_subquery))
                    .group_by(NodeNgram.ngram_id)
                    .all()
                   )

    # -------------------------------------------------
    tfidfs = {}
    log_tot_docs = log(total_docs)
    for (ngram_id, tf, nd) in tf_nd:
        # tfidfs[ngram_id] = tf * log(total_docs/nd)
        tfidfs[ngram_id] = tf * (log_tot_docs-log(nd))
    # -------------------------------------------------

    if overwrite_id:
        the_id = overwrite_id
    else:
        # create the new TFIDF-XXXX node
        tfidf_nd = corpus.add_child()
        if scope == "local":            # TODO discuss use and find new typename
            tfidf_nd.typename  = "TFIDF-CORPUS"
            tfidf_nd.name      = "tfidf-cumul-corpus (in:%s)" % corpus.id
        elif scope == "global":
            tfidf_nd.typename  = "TFIDF-GLOBAL"
            tfidf_nd.name      = "tfidf-cumul-global (in type:%s)" % this_source_type
        session.add(tfidf_nd)
        session.commit()
        the_id = tfidf_nd.id

    # reflect that in NodeNodeNgrams
    # £TODO replace bulk_insert by something like WeightedContextMatrix.save()
    bulk_insert(
        NodeNodeNgram,
        ('node1_id', 'node2_id','ngram_id', 'score'),
        ((the_id,    corpus.id,    ng,   tfidfs[ng]) for ng in tfidfs)
    )

    return the_id



def compute_tfidf_local(corpus, overwrite_id=None):
    """
    Calculates tfidf similarity of each (doc, ngram) couple, within the current corpus

    Parameters:
      - the corpus itself
      - overwrite_id: optional id of a pre-existing TFIDF-XXXX node for this corpus
                   (the Node and its previous NodeNodeNgram rows will be replaced)
    """

    # All docs of this corpus
    docids_subquery = (session
                        .query(Node.id)
                        .filter(Node.parent_id == corpus.id)
                        .filter(Node.typename == "DOCUMENT")
                        .subquery()
                       )

    # N
    total_docs = session.query(docids_subquery).count()

    # number of docs with given term (number of rows = M ngrams)
    n_docswith_ng = (session
                    .query(
                        NodeNgram.ngram_id,
                        func.count(NodeNgram.node_id).label("nd")  # nd: n docs with term
                     )
                    .filter(NodeNgram.node_id.in_(docids_subquery))
                    .group_by(NodeNgram.ngram_id)
                    .all()
                   )

    # { ngram_id => log(nd) }
    log_nd_lookup = {row.ngram_id : log(row.nd) for row in n_docswith_ng}

    # tf for each couple (number of rows = N docs X M ngrams)
    tf_doc_ng = (session
                    .query(
                        NodeNgram.ngram_id,
                        NodeNgram.node_id,
                        func.sum(NodeNgram.weight).label("tf"),    # tf: occurrences
                     )
                    .filter(NodeNgram.node_id.in_(docids_subquery))
                    .group_by(NodeNgram.node_id, NodeNgram.ngram_id)
                    .all()
                   )

    # ---------------------------------------------------------
    tfidfs = {}
    log_tot_docs = log(total_docs)
    for (ngram_id, node_id, tf) in tf_doc_ng:
        log_nd = log_nd_lookup[ngram_id]
        # tfidfs[ngram_id] = tf * log(total_docs/nd)
        tfidfs[node_id, ngram_id] = tf * (log_tot_docs-log_nd)
    # ---------------------------------------------------------

    if overwrite_id:
        the_id = overwrite_id
    else:
        # create the new TFIDF-CORPUS node
        tfidf_node = corpus.add_child()
        tfidf_node.typename  = "TFIDF-CORPUS"
        tfidf_node.name      = "tfidf-sims-corpus (in:%s)" % corpus.id
        session.add(tfidf_node)
        session.commit()
        the_id = tfidf_node.id

    # reflect that in NodeNodeNgrams
    # £TODO replace bulk_insert by something like WeightedContextMatrix.save()
    bulk_insert(
        NodeNodeNgram,
        ('node1_id', 'node2_id','ngram_id', 'score'),
        ((the_id,    node_id,    ngram_id,   tfidfs[node_id,ngram_id]) for (node_id, ngram_id) in tfidfs)
    )

    return the_id
