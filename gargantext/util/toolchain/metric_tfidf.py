"""
Computes ngram scores with 3 ranking functions:
   - the simple sum of occurrences inside the corpus
   - the tfidf inside the corpus
   - the global tfidf for all corpora having same source

FIXME: "having the same source" means we need to select inside hyperdata
       with a (perhaps costly) JSON query: WHERE hyperdata->'resources' @> ...
"""

from gargantext.models   import Node, NodeNgram, NodeNodeNgram, NodeNgramNgram
from gargantext.util.db  import session, bulk_insert, aliased, \
                                func # = sqlalchemy.func like sum() or count()
from sqlalchemy.sql.expression import case # for choice if ngram has mainform or not
from sqlalchemy import distinct   # for list of unique ngram_ids within a corpus
from math                import log
# £TODO
# from gargantext.util.lists import WeightedContextIndex


def compute_occs(corpus, overwrite_id = None, groupings_id = None,):
    """
    Calculates sum of occs per ngram (or per mainform if groups) within corpus
                 (used as info in the ngrams table view)

    ? optimize ?  OCCS here could be calculated simultaneously within TFIDF-CORPUS loop

    ? use cases ?
       => not the main score for users (their intuition for nb of docs having word)
       => but is the main weighting value for any NLP task

    Parameters:
        - overwrite_id: optional id of a pre-existing OCCURRENCES node for this corpus
                     (the Node and its previous NodeNodeNgram rows will be replaced)
        - groupings_id: optional id of a GROUPLIST node for this corpus
                        IF absent the occurrences are the sums for each ngram
                        IF present they're the sums for each ngram's mainform
    """
    #  simple case : no groups
    #                ---------
    #    (the occurrences are the sums for each ngram)
    if not groupings_id:

        # NodeNgram index
        occs_q = (session
                    .query(
                        NodeNgram.ngram_id,
                        func.sum(NodeNgram.weight)   # <== OCCURRENCES
                     )
                     # filter docs within corpus
                    .join(Node)
                    .filter(Node.parent_id == corpus.id)
                    .filter(Node.typename == "DOCUMENT")

                    # for the sum
                    .group_by(NodeNgram.ngram_id)
                   )


    #   difficult case: with groups
    #                   ------------
    # (the occurrences are the sums for each ngram's mainform)
    else:
        # sub-SELECT the synonyms of this GROUPLIST id (for OUTER JOIN later)
        syn = (session.query(NodeNgramNgram.ngram1_id,
                             NodeNgramNgram.ngram2_id)
                .filter(NodeNgramNgram.node_id == groupings_id)
                .subquery()
               )

        # NodeNgram index with additional subform => mainform replacement
        occs_q = (session
                    .query(
                        # intermediate columns for debug
                        # -------------------------------
                        # NodeNgram.node_id,        # document
                        # NodeNgram.ngram_id,       # <= the occurring ngram
                        # NodeNgram.weight,         # <= its frequency in doc
                        # syn.c.ngram1_id           # mainform
                        # syn.c.ngram2_id,          # subform

                        # ngram to count aka counted_form
                        # ----------------------------------
                        #     either NodeNgram.ngram_id as before
                        #         or mainform if it exists
                        case([(syn.c.ngram1_id != None, syn.c.ngram1_id)],
                             else_=NodeNgram.ngram_id)
                        .label("counted_form"),

                        # the sum itself
                        # --------------
                        func.sum(NodeNgram.weight)   # <== OCCURRENCES
                    )
                    # this brings the mainform if NodeNgram.ngram_id has one in syn
                    .outerjoin(syn,
                               syn.c.ngram2_id == NodeNgram.ngram_id)

                    # filter docs within corpus
                    .join(Node)
                    .filter(Node.parent_id == corpus.id)
                    .filter(Node.typename == "DOCUMENT")

                    # for the sum
                    .group_by("counted_form")
                 )


    occ_sums = occs_q.all()
    # example result = [(1970, 1.0), (2024, 2.0),  (259, 2.0), (302, 1.0), ... ]
    #                    ^^^^  ^^^
    #                ngram_id   sum_wei
    #                   OR
    #              counted_form

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


def compute_ti_ranking(corpus, count_scope="local", termset_scope="local", overwrite_id=None):
    """
    # TODO check if cumulated tfs correspond to app's use cases and intention

    Calculates tfidf ranking (cumulated tfidf for each ngram) within given scope

    Parameters:
      - the corpus itself
      - count_scope: {"local" or "global"}
         - local  <=> frequencies counted in the current corpus
         - global <=> frequencies counted in all corpora of this type

        when the count_scope is global, there is another parameter:
          - termset_scope: {"local" or "global"}
             - local <=> output list of terms limited to the current corpus
               (SELECT DISTINCT ngram_id FROM nodes_ngrams WHERE node_id IN <docs>)
             - global <=> output list of terms from all corpora of this type
                                                    !!!! (many more terms)

      - overwrite_id: optional id of a pre-existing TFIDF-XXXX node for this corpus
                   (the Node and its previous NodeNodeNgram rows will be replaced)
    """

    # MAIN QUERY SKELETON
    tf_nd_query = (session
                    .query(
                        NodeNgram.ngram_id,
                        func.sum(NodeNgram.weight),    # tf: same as occurrences
                                                       # -----------------------

                        func.count(NodeNgram.node_id)  # nd: n docs with term
                                                       # --------------------
                     )
                    .group_by(NodeNgram.ngram_id)

                    # optional *count_scope*: if we'll restrict the doc nodes
                    #          -------------
                    # .join(countdocs_subquery,
                    #       countdocs_subquery.c.id == NodeNgram.node_id)

                    # optional *termset_scope*: if we'll restrict the ngrams
                    #          ---------------
                    # .join(termset_subquery,
                    #       termset_subquery.c.uniq_ngid == NodeNgram.ngram_id)
                   )

    # validate string params
    if count_scope not in ["local","global"]:
        raise ValueError("compute_ti_ranking: count_scope param allowed values: 'local', 'global'")
    if termset_scope not in ["local","global"]:
        raise ValueError("compute_ti_ranking: termset_scope param allowed values: 'local', 'global'")
    if count_scope == "local" and termset_scope == "global":
        raise ValueError("compute_ti_ranking: the termset_scope param can be 'global' iff count_scope param is 'global' too.")

    # local <=> within this corpus
    if count_scope == "local":
        # All docs of this corpus
        countdocs_subquery = (session
                        .query(Node.id)
                        .filter(Node.typename == "DOCUMENT")
                        .filter(Node.parent_id == corpus.id)
                        .subquery()
                       )

        # both scopes are the same: no need to independantly restrict the ngrams
        tf_nd_query = tf_nd_query.join(countdocs_subquery,
                                       countdocs_subquery.c.id == NodeNgram.node_id)


    # global <=> within all corpora of this source
    elif count_scope == "global":
        this_source_type = corpus.resources()[0]['type']

        CorpusNode = aliased(Node)

        # All docs **in all corpora of the same source**
        countdocs_subquery = (session
                        .query(Node.id)
                        .filter(Node.typename == "DOCUMENT")

                        # join on parent_id with selected corpora nodes
                        .join(CorpusNode, CorpusNode.id == Node.parent_id)
                        .filter(CorpusNode.typename == "CORPUS")
                        .filter(CorpusNode.hyperdata['resources'][0]['type'].astext == str(this_source_type))
                        .subquery()
                       )

        if termset_scope == "global":
            # both scopes are the same: no need to independantly restrict the ngrams
            tf_nd_query = tf_nd_query.join(countdocs_subquery,
                                           countdocs_subquery.c.id == NodeNgram.node_id)

        elif termset_scope == "local":

            # All unique terms in the original corpus
            termset_subquery = (session
                            .query(distinct(NodeNgram.ngram_id).label("uniq_ngid"))
                            .join(Node)
                            .filter(Node.typename == "DOCUMENT")
                            .filter(Node.parent_id == corpus.id)
                            .subquery()
                           )

            # only case of independant restrictions on docs and terms
            tf_nd_query = (tf_nd_query
                            .join(countdocs_subquery,
                                  countdocs_subquery.c.id == NodeNgram.node_id)
                            .join(termset_subquery,
                                  termset_subquery.c.uniq_ngid == NodeNgram.ngram_id)
                          )

    # N
    total_docs = session.query(countdocs_subquery).count()

    # result
    tf_nd = tf_nd_query.all()

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
        if count_scope == "local":            # TODO discuss use and find new typename
            tfidf_nd.typename  = "TFIDF-CORPUS"
            tfidf_nd.name      = "tfidf-cumul-corpus (in:%s)" % corpus.id
        elif count_scope == "global":
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
