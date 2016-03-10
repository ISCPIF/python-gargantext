from gargantext.models   import Node, NodeNgram, NodeNodeNgram
from gargantext.util.db  import session, bulk_insert
from sqlalchemy import text
# £TODO
# from gargantext.util.lists import WeightedContextIndex

from gargantext.util.db import func # = sqlalchemy.func like sum() or count()

from math  import log

def compute_occurrences_local(corpus):
    """
    Calculates sum of occs per ngram within corpus
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

    # create the new OCCURRENCES node
    occnode = Node()
    occnode.typename  = "OCCURRENCES"
    occnode.name      = "occ_sums (in:%s)" % corpus.id
    occnode.parent_id = corpus.id
    occnode.user_id   = corpus.user_id
    session.add(occnode)
    session.commit()

    # reflect that in NodeNodeNgrams (could be NodeNgram but harmony with tfidf)
    # £TODO replace bulk_insert by something like WeightedContextMatrix.save()
    bulk_insert(
        NodeNodeNgram,
        ('node1_id' , 'node2_id', 'ngram_id', 'score'),
        ((occnode.id, corpus.id,  res[0], res[1]) for res in occ_sums)
    )

    return occnode.id


def compute_tfidf(corpus, scope="local"):
    """
    Calculates tfidf within the current corpus

    Parameter:
      - scope: {"local" or "global"}
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

    # create the new TFIDF-CORPUS node
    tfidf_nd = Node(parent_id = corpus.id, user_id = corpus.user_id)
    if scope == "local":
        tfidf_nd.typename  = "TFIDF-CORPUS"
        tfidf_nd.name      = "tfidf-c (in:%s)" % corpus.id
    elif scope == "global":
        tfidf_nd.typename  = "TFIDF-GLOBAL"
        tfidf_nd.name      = "tfidf-g (in type:%s)" % this_source_type
    session.add(tfidf_nd)
    session.commit()

    # reflect that in NodeNodeNgrams
    # £TODO replace bulk_insert by something like WeightedContextMatrix.save()
    bulk_insert(
        NodeNodeNgram,
        ('node1_id' , 'node2_id', 'ngram_id', 'score'),
        ((tfidf_nd.id,  corpus.id,     ng, tfidfs[ng]) for ng in tfidfs)
    )

    return tfidf_nd.id
