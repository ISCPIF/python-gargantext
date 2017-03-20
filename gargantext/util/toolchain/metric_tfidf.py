"""
Computes ngram scores with 3 ranking functions:
   - the simple sum of occurrences inside the corpus
   - the tfidf inside the corpus
   - the global tfidf for all corpora having same source

FIXME: "having the same source" means we need to select inside hyperdata
       with a (perhaps costly) JSON query: WHERE hyperdata->'resources' @> ...
"""

from gargantext.models   import Node, NodeNgram, NodeNodeNgram, NodeNgramNgram
from gargantext.util.db_cache  import cache
from gargantext.util.db  import session, bulk_insert, aliased, \
                                func # = sqlalchemy.func like sum() or count()
from sqlalchemy.sql.expression import case # for choice if ngram has mainform or not
from sqlalchemy import distinct   # for list of unique ngram_ids within a corpus
from math                import log
from re                  import match
from datetime             import datetime
# £TODO
# from gargantext.util.lists import WeightedIndex

def t():
    return datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

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
        - groupings_id: optional id of a GROUPLIST node for these ngrams
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

    #print(str(occs_q.all()))
    occ_sums = occs_q.all()
    # example result = [(1970, 1.0), (2024, 2.0),  (259, 2.0), (302, 1.0), ... ]
    #                    ^^^^  ^^^
    #                ngram_id   sum_wei
    #                   OR
    #              counted_form

    if overwrite_id:
        # overwrite pre-existing id
        the_id = overwrite_id
        session.query(NodeNodeNgram).filter(NodeNodeNgram.node1_id == the_id).delete()
        session.commit()
    else:
        # create the new OCCURRENCES node
        occnode = corpus.add_child(
            typename  = "OCCURRENCES",
            name = "occ_sums (in:%s)" % corpus.id
        )
        session.add(occnode)
        session.commit()
        the_id = occnode.id

    # £TODO  make it NodeNgram instead NodeNodeNgram ! and rebase :/
    #        (idem ti_ranking)
    bulk_insert(
        NodeNodeNgram,
        ('node1_id' , 'node2_id', 'ngram_id', 'score'),
        ((the_id, corpus.id,  res[0], res[1]) for res in occ_sums)
    )

    return the_id


def compute_ti_ranking(corpus,
                       groupings_id = None,
                       count_scope="local", termset_scope="local",
                       overwrite_id=None):
    """
    Calculates tfidf ranking within given scope
                ----------
                   |
            via weighting of
            cumulated tfidf  --------- Sum{i}(tf_ij) * ln(N/|U{i}(docs{mot€d})|)
             per ngram ng_i
         (or per mainform ng_i' if groups)
           across some docs d_j

    Parameters:
      - the corpus itself (or corpus_id)
      - groupings_id: optional id of a GROUPLIST node for these ngrams
                        IF absent the ti weights are the sums for each ngram
                        IF present they're the sums for each ngram's mainform

      - count_scope: {"local" or "global"}
         - local  <=> frequencies counted in the current corpus
         - global <=> frequencies counted in all corpora of this type

        when the count_scope is global, there is another parameter:
          - termset_scope: {"local" or "global"}
             - local <=> output list of terms limited to the current corpus
               (SELECT DISTINCT ngram_id FROM nodes_ngrams WHERE node_id IN <docs>)
             - global <=> output list of terms found in global doc scope
                                                    !!!! (many more terms)

      - overwrite_id: optional id of a pre-existing XXXX node for this corpus
                   (the Node and its previous Node NodeNgram rows will be replaced)
    """
    print("compute_ti_ranking")
    # validate string params
    if count_scope not in ["local","global"]:
        raise ValueError("compute_ti_ranking: count_scope param allowed values: 'local', 'global'")
    if termset_scope not in ["local","global"]:
        raise ValueError("compute_ti_ranking: termset_scope param allowed values: 'local', 'global'")
    if count_scope == "local" and termset_scope == "global":
        raise ValueError("compute_ti_ranking: the termset_scope param can be 'global' iff count_scope param is 'global' too.")

    # get corpus
    if type(corpus) == int:
        corpus_id = corpus
        corpus = cache.Node[corpus_id]
    elif type(corpus) == str and match(r'^\d+$', corpus):
        corpus_id = int(corpus)
        corpus = cache.Node[corpus_id]
    else:
        # assuming Node class
        corpus_id = corpus.id

    # prepare sqla mainform vs ngram selector
    ngform_i = None

    if not groupings_id:
        ngform_i = NodeNgram.ngram_id

    else:
        # prepare translations
        syno = (session.query(NodeNgramNgram.ngram1_id,
                             NodeNgramNgram.ngram2_id)
                .filter(NodeNgramNgram.node_id == groupings_id)
                .subquery()
               )
        # cf commentaire détaillé dans compute_occs() + todo facto

        ngform_i = case([
                            (syno.c.ngram1_id != None, syno.c.ngram1_id),
                            (syno.c.ngram1_id == None, NodeNgram.ngram_id)
                            #     condition               value
                        ])

    # MAIN QUERY SKELETON
    tf_nd_query = (session
                    .query(
                        # NodeNgram.ngram_id
                        # or similar if grouping ngrams under their mainform
                        ngform_i.label("counted_ngform"),

                        # the tfidf elements
                        # ------------------
                        func.sum(NodeNgram.weight),    # tf: same as occurrences
                                                       # -----------------------

                        func.count(NodeNgram.node_id)  # nd: n docs with term
                                                       # --------------------
                     )
                    .group_by("counted_ngform")

                    # count_scope to specify in which doc nodes to count
                    # -----------
                    # .join(countdocs_subquery,
                    #       countdocs_subquery.c.id == NodeNgram.node_id)

                    # optional termset_scope: if we'll restrict the ngrams
                    #          -------------
                    # .join(termset_subquery,
                    #       termset_subquery.c.uniq_ngid == NodeNgram.ngram_id)

                    # optional translations to bring the subform's replacement
                    #          ------------
                    # .outerjoin(syno,
                    #           syno.c.ngram2_id == NodeNgram.ngram_id)
                   )



    # TUNING THE QUERY

    if groupings_id:
        tf_nd_query = tf_nd_query.outerjoin(
                                        syno,
                                        syno.c.ngram2_id == NodeNgram.ngram_id
                                        )

    # local <=> within this corpus
    if count_scope == "local":
        # All docs of this corpus
        countdocs_subquery = (session
                        .query(Node.id)
                        .filter(Node.typename == "DOCUMENT")
                        .filter(Node.parent_id == corpus_id)
                        .subquery()
                       )

        # no need to independantly restrict the ngrams
        tf_nd_query = tf_nd_query.join(countdocs_subquery,
                                       countdocs_subquery.c.id == NodeNgram.node_id)
        # ---

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
                        # TODO index corpus_sourcetype in DB
                        .filter(CorpusNode.hyperdata['resources'][0]['type'].astext == str(this_source_type))
                        .subquery()
                       )

        if termset_scope == "global":
            # both scopes are the same: no need to independantly restrict the ngrams
            tf_nd_query = tf_nd_query.join(countdocs_subquery,
                                           countdocs_subquery.c.id == NodeNgram.node_id)
            # ---

        elif termset_scope == "local":

            # All unique terms...
            termset_subquery = (session
                            .query(
                                distinct(NodeNgram.ngram_id).label("uniq_ngid")
                              )
                            # ... in the original corpus
                            .join(Node)
                            .filter(Node.typename == "DOCUMENT")
                            .filter(Node.parent_id == corpus_id)
                            .subquery()
                           )

            # only case of independant restrictions on docs and terms
            tf_nd_query = (tf_nd_query
                            .join(countdocs_subquery,
                                  countdocs_subquery.c.id == NodeNgram.node_id)
                            .join(termset_subquery,
                                  termset_subquery.c.uniq_ngid == NodeNgram.ngram_id)
                          )
            # ---

    # M
    total_docs = session.query(countdocs_subquery).count()
    log_tot_docs = log(total_docs)

    # result
    print("%s : Starting Query tf_nd_query" % t())
    #print(str(tf_nd_query.all()))
    tf_nd = tf_nd_query.all()
    print("%s : End Query tf_nd_quer" % t())

    # -------------- "sommatoire" sur mot i ----------------
    print("%s : tfidfsum" % t())
    tfidfsum = {}
    for (ngram_i, tf_i, nd_i) in tf_nd:
        # tfidfsum[ngram_i] = tf_i * log(total_docs/nd_i)
        tfidfsum[ngram_i] = tf_i * (log_tot_docs-log(nd_i))
    # ------------------------------------------------------

    # N pour info
    total_ngramforms = len(tfidfsum)

    if overwrite_id:
        the_id = overwrite_id
        session.query(NodeNodeNgram).filter(NodeNodeNgram.node1_id == the_id).delete()
        session.commit()
    else:
        # create the new TFIDF-XXXX node to get an id
        tir_nd = corpus.add_child()
        if count_scope == "local":
            tir_nd.typename  = "TIRANK-CORPUS"
            tir_nd.name      = "ti rank (%i ngforms in corpus:%s)" % (
                                     total_ngramforms, corpus_id)
        elif count_scope == "global":
            tir_nd.typename  = "TIRANK-GLOBAL"
            tir_nd.name      = "ti rank (%i ngforms %s in corpora of sourcetype:%s)" % (
                                       total_ngramforms,
                                       ("from corpus %i" % corpus_id) if (termset_scope == "local") else "" ,
                                       this_source_type)

        session.add(tir_nd)
        session.commit()
        the_id = tir_nd.id


    # TODO 1 discuss use and find new typename
    # TODO 2 release these 2 typenames TFIDF-CORPUS and TFIDF-GLOBAL
    # TODO 3 recreate them elsewhere in their sims (WeightedIndex) version
    # TODO 4 requalify this here as a NodeNgram
    # TODO 5 use WeightedList.save()

    # reflect that in NodeNodeNgrams
    bulk_insert(
        NodeNodeNgram,
        ('node1_id', 'node2_id','ngram_id', 'score'),
        ((the_id,  corpus_id,    ng,   tfidfsum[ng]) for ng in tfidfsum)
    )

    return the_id


def compute_tfidf_local(corpus,
                        on_list_id=None,
                        groupings_id=None,
                        overwrite_id=None):
    """
    Calculates tfidf similarity of each (doc, ngram) couple, within the current corpus

    Parameters:
      - the corpus itself
      - groupings_id: optional synonym relations to add all subform counts
                      with their mainform's counts
      - on_list_id: mainlist or maplist type, to constrain the input ngrams
      - overwrite_id: optional id of a pre-existing TFIDF-XXXX node for this corpus
                   (the Node and its previous NodeNodeNgram rows will be replaced)
    """
    print("Compute TFIDF local")
    
    # All docs of this corpus
    docids_subquery = (session
                        .query(Node.id)
                        .filter(Node.parent_id == corpus.id)
                        .filter(Node.typename == "DOCUMENT")
                        .subquery()
                       )

    # N
    total_docs = session.query(docids_subquery).count()


    # define the counted form
    if not groupings_id:
        ngform_id = NodeNgram.ngram_id
    else:
        Syno = (session.query(NodeNgramNgram.ngram1_id,
                             NodeNgramNgram.ngram2_id)
                .filter(NodeNgramNgram.node_id == groupings_id)
                .subquery()
               )

        ngform_id = case([
                            (Syno.c.ngram1_id != None, Syno.c.ngram1_id),
                            (Syno.c.ngram1_id == None, NodeNgram.ngram_id)
                        ])

    # tf for each couple (number of rows = N docs X M ngrams)
    tf_doc_query = (session
                    .query(
                        ngform_id,
                        NodeNgram.node_id,
                        func.sum(NodeNgram.weight).label("tf"),    # tf: occurrences
                     )

                     # select within docs of current corpus
                    .join(docids_subquery,
                          docids_subquery.c.id == NodeNgram.node_id)
                   )

    if groupings_id:
        tf_doc_query = ( tf_doc_query
                .outerjoin(Syno, Syno.c.ngram2_id == NodeNgram.ngram_id)
            )
        # now when we'll group_by the ngram2 freqs will be added to ngram1

    if on_list_id:
        Miamlist = aliased(NodeNgram)
        tf_doc_query = ( tf_doc_query
                .join(Miamlist, Miamlist.ngram_id == ngform_id)
                .filter( Miamlist.node_id == on_list_id )
            )

    # execute query to do our tf sum
    tf_per_doc = tf_doc_query.group_by(NodeNgram.node_id, ngform_id).all()

    # ex: [(128371, 9732, 1.0),
    #      (128383, 9740, 1.0),
    #      (128373, 9731, 1.0),
    #      (128376, 9734, 1.0),
    #      (128372, 9731, 1.0),
    #      (128383, 9733, 1.0),
    #      (128383, 9735, 1.0),
    #      (128389, 9734, 1.0),
    #      (8624, 9731, 1.0),
    #      (128382, 9740, 1.0),
    #      (128383, 9739, 1.0),
    #      (128383, 9736, 1.0),
    #      (128378, 9735, 1.0),
    #      (128375, 9733, 4.0),
    #      (128383, 9732, 1.0)]
    #        ^ ^     ^^    ^^
    #       ngram   doc   freq in this doc



    # simultaneously count docs with given term (number of rows = M ngrams)

    ndocswithngram = {}
    for triple in tf_per_doc:
        ng = triple[0]
        doc = triple[1]
        if ng in ndocswithngram:
            ndocswithngram[ng] += 1
        else:
            ndocswithngram[ng] = 1

    # print(ndocswithngram)

    # store for use in formula
    # { ngram_id => log(nd) }
    log_nd_lookup = {ng : log(nd_count)
                        for (ng, nd_count) in ndocswithngram.items()}


    # ---------------------------------------------------------
    tfidfs = {}
    log_tot_docs = log(total_docs)
    for (ngram_id, node_id, tf) in tf_per_doc:
        log_nd = log_nd_lookup[ngram_id]
        # tfidfs[ngram_id] = tf * log(total_docs/nd)
        tfidfs[node_id, ngram_id] = tf * (log_tot_docs-log_nd)
    # ---------------------------------------------------------

    if overwrite_id:
        the_id = overwrite_id
        session.query(NodeNodeNgram).filter(NodeNodeNgram.node1_id == the_id).delete()
        session.commit()
    else:
        # create the new TFIDF-CORPUS node
        tfidf_node = corpus.add_child()
        tfidf_node.typename  = "TFIDF-CORPUS"
        tfidf_node.name      = "tfidf-sims-corpus (in:%s)" % corpus.id
        session.add(tfidf_node)
        session.commit()
        the_id = tfidf_node.id

    # reflect that in NodeNodeNgrams
    # £TODO replace bulk_insert by something like WeightedIndex.save()
    bulk_insert(
        NodeNodeNgram,
        ('node1_id', 'node2_id','ngram_id', 'score'),
        ((the_id,    node_id,    ngram_id,   tfidfs[node_id,ngram_id]) for (node_id, ngram_id) in tfidfs)
    )

    return the_id
