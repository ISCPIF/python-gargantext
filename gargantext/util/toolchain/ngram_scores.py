from gargantext.models   import Node, NodeNgram, NodeNodeNgram
from gargantext.util.db  import session, bulk_insert

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


def compute_tfidf_local(corpus):
    """
    Calculates tfidf within the current corpus
    """

    # ?? FIXME could we keep the docids somehow from previous computations ??
    docids_subquery = (session
                        .query(Node.id)
                        .filter(Node.parent_id == corpus.id)
                        .filter(Node.typename == "DOCUMENT")
                        .subquery()
                       )

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

    # ---------------------------------------------
    tfidfs = {}
    for (ngram_id, tf, nd) in tf_nd:
        tfidfs[ngram_id] = tf / log(total_docs/nd)
    # ---------------------------------------------

    # create the new TFIDF-CORPUS node
    ltfidf = Node()
    ltfidf.typename  = "TFIDF-CORPUS"
    ltfidf.name      = "tfidf (in:%s)" % corpus.id
    ltfidf.parent_id = corpus.id
    ltfidf.user_id   = corpus.user_id
    session.add(ltfidf)
    session.commit()

    # reflect that in NodeNodeNgrams
    # £TODO replace bulk_insert by something like WeightedContextMatrix.save()
    bulk_insert(
        NodeNodeNgram,
        ('node1_id' , 'node2_id', 'ngram_id', 'score'),
        ((ltfidf.id,  corpus.id,     ng, tfidfs[ng]) for ng in tfidfs)
    )

    return ltfidf.id
