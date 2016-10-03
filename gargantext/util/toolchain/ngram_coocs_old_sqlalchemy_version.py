"""
COOCS
    (this is the full sqlalchemy version, from "refactored" toolchain march-may 2016)
"""
from gargantext.models         import Node, NodeNgram, NodeNgramNgram, \
                                      NodeHyperdata, Ngram
from gargantext.util.lists     import WeightedMatrix
from gargantext.util.db        import session, aliased, func
from gargantext.util.db_cache  import cache
from gargantext.constants      import DEFAULT_COOC_THRESHOLD
from datetime                  import datetime

from sqlalchemy.sql.expression import case # for choice if ngram has mainform or not

def compute_coocs(  corpus,
                    overwrite_id    = None,
                    just_pass_result= True,   # just return the WeightedMatrix,
                                              #    (don't write to DB)
                    threshold       = DEFAULT_COOC_THRESHOLD,
                    groupings_id    = None,
                    on_list_id      = None,
                    stoplist_id     = None,
                    start           = None,
                    end             = None,
                    symmetry_filter = False,
                    diagonal_filter = True):
    """
    Count how often some extracted terms appear
    together in a small context (document)
    throughout a larger context (corpus).

             [NodeNgram]                       [NodeNgramNgram]

    node_id | ngram_id | weight       ngram1_id | ngram2_id | score |
    --------+----------+--------      ----------+-----------+-------+
     MyDocA |      487 |      1   =>        487 |       294 |     2 |
     MyDocA |      294 |      3
     MyDocB |      487 |      1
     MyDocB |      294 |      4

    Fill that info in DB:
      - a *new* COOCCURRENCES node
      - and all corresponding NodeNgramNgram rows

    worse case complexity ~ O(N²/2) with N = number of ngrams

    If a mainlist is provided, we filter doc ngrams to those also in the list.

    Parameters:
      - the corpus node
      - overwrite_id: id of a pre-existing COOCCURRENCES node for this corpus
                     (all hyperdata and previous NodeNgramNgram rows will be replaced)
      - threshold: on output cooc count (previously called hapax)
      - groupings_id: optional synonym relations to add all subform counts
                      with their mainform's counts
      - on_list_id: mainlist or maplist type, to constrain the input ngrams
      - stoplist_id: stoplist for filtering input ngrams
                     (normally unnecessary if a mainlist is already provided)
      - start, end: provide one or both temporal limits to filter on doc date
                    NB the expected type of parameter value is datetime.datetime
                        (string is also possible but format must follow
                          this convention: "2001-01-01" aka "%Y-%m-%d")
      - symmetry_filter: prevent calculating where ngram1_id  > ngram2_id
      - diagonal_filter: prevent calculating where ngram1_id == ngram2_id


     (deprecated parameters)
      - field1,2: allowed to count other things than ngrams (eg tags) but no use case at present
      - isMonopartite: ?? used a nodes_hyperdata_ngrams table ???

    basic idea for one doc
    ======================
    each pair of ngrams sharing same doc (node_id)
        SELEC idxa.ngram_id, idxb.ngram_id
        FROM nodes_ngrams AS idxa
        ---------------------------------
        JOIN nodes_ngrams AS idxb
        ON idxa.node_id = idxb.node_id      <== that's cooc
        ---------------------------------
        AND idxa.ngram_id <> idxb.ngram_id   (diagonal_filter)
        AND idxa.node_id = MY_DOC ;

    on entire corpus
    =================
    coocs for each doc :
      - each given pair like (termA, termB) will likely appear several times
        => we do GROUP BY (Xindex.ngram_id, Yindex.ngram_id)
      - we count unique appearances of the pair (cooc)


    """

        #   - TODO cvalue_id: allow a metric as additional  input filter
        #   - TODO n_min, n_max : filter on Ngram.n (aka length of ngram)
        #   - TODO weighted: if False normal cooc to be saved as result
        #                    if True  weighted cooc (experimental)

    # /!\ big combinatorial complexity /!\
    # pour 8439 lignes dans l'index nodes_ngrams dont 1442 avec occ > 1
    #  1.859.408 lignes pour la requête cooc simple
    #     71.134 lignes en se limitant aux ngrammes qui ont une occ > 1 (weight)

    # 2 x the occurrence index table
    Xindex = aliased(NodeNgram)
    Yindex = aliased(NodeNgram)

    # for debug (1/4)
    # Xngram = aliased(Ngram)
    # Yngram = aliased(Ngram)

    # 1) prepare definition of counted forms
    if not groupings_id:

        # no groupings => the counted forms are the ngrams
        Xindex_ngform_id = Xindex.ngram_id
        Yindex_ngform_id = Yindex.ngram_id


    # groupings: cf commentaire détaillé dans compute_occs() + todo facto
    else:
        # prepare translations
        Xsyno = (session.query(NodeNgramNgram.ngram1_id,
                             NodeNgramNgram.ngram2_id)
                .filter(NodeNgramNgram.node_id == groupings_id)
                .subquery()
               )

        # further use as anon tables prevent doing Ysyno = Xsyno
        Ysyno = (session.query(NodeNgramNgram.ngram1_id,
                             NodeNgramNgram.ngram2_id)
                .filter(NodeNgramNgram.node_id == groupings_id)
                .subquery()
               )

        # groupings => define the counted form depending on the existence of a synonym
        Xindex_ngform_id = case([
                            (Xsyno.c.ngram1_id != None, Xsyno.c.ngram1_id),
                            (Xsyno.c.ngram1_id == None, Xindex.ngram_id)
                            #     condition               value
                        ])

        Yindex_ngform_id = case([
                            (Ysyno.c.ngram1_id != None, Ysyno.c.ngram1_id),
                            (Ysyno.c.ngram1_id == None, Yindex.ngram_id)
                        ])
        # ---



    # 2) BASE DB QUERY

    # cooccurrences columns definition ----------------
    ucooc = func.count(Xindex_ngform_id).label("ucooc")
    # NB could be X or Y in this line
    #    (we're counting grouped rows and just happen to do it on this column)
    base_query = (
        session.query(
                    Xindex_ngform_id,
                    Yindex_ngform_id,
                    ucooc

                    # for debug (2/4)
                    # , Xngram.terms.label("w_x")
                    # , Yngram.terms.label("w_y")
                    )
               .join(Yindex, Xindex.node_id == Yindex.node_id )   # <- by definition of cooc

               .join(Node, Node.id == Xindex.node_id) # <- b/c within corpus
               .filter(Node.parent_id == corpus.id)   # <- b/c within corpus
               .filter(Node.typename == "DOCUMENT")   # <- b/c within corpus
        )

    # outerjoin the synonyms if needed
    if groupings_id:
        base_query = (base_query
               .outerjoin(Xsyno,                 # <- synonyms for Xindex.ngrams
                          Xsyno.c.ngram2_id == Xindex.ngram_id)
               .outerjoin(Ysyno,                 # <- synonyms for Yindex.ngrams
                          Ysyno.c.ngram2_id == Yindex.ngram_id)
            )


    # 3) counting clause in any case
    coocs_query = (base_query
               .group_by(
                    Xindex_ngform_id, Yindex_ngform_id # <- what we're counting
                    # for debug (3/4)
                    # ,"w_x", "w_y"
                    )

            # for debug (4/4)
            # .join(Xngram, Xngram.id == Xindex_ngform_id)
            # .join(Yngram, Yngram.id == Yindex_ngform_id)

            .order_by(ucooc)
           )


    # 4) INPUT FILTERS (reduce N before O(N²))
    if on_list_id:
        # £TODO listes différentes ou bien une liste pour x et tous les ngrammes pour y
        #       car permettrait expansion de liste aux plus proches voisins (MacLachlan)
        #       (avec une matr rectangulaire)

        m1 = aliased(NodeNgram)
        m2 = aliased(NodeNgram)

        coocs_query = ( coocs_query
            .join(m1, m1.ngram_id == Xindex_ngform_id)
            .join(m2, m2.ngram_id == Yindex_ngform_id)

            .filter( m1.node_id == on_list_id )
            .filter( m2.node_id == on_list_id )
        )

    if stoplist_id:
        s1 = (session.query(NodeNgram.ngram_id)
                .filter(NodeNgram.node_id == stoplist_id)
                .subquery()
               )

        # further use as anon tables prevent doing s2 = s1
        s2 = (session.query(NodeNgram.ngram_id)
                .filter(NodeNgram.node_id == stoplist_id)
                .subquery()
               )

        coocs_query = ( coocs_query
            .outerjoin(s1, s1.c.ngram_id == Xindex_ngform_id)
            .outerjoin(s2, s2.c.ngram_id == Yindex_ngform_id)

            # équivalent NOT IN stoplist
            .filter( s1.c.ngram_id == None )
            .filter( s2.c.ngram_id == None )

        )

    if diagonal_filter:
        # don't compute ngram with itself
        coocs_query = coocs_query.filter(Xindex_ngform_id != Yindex_ngform_id)

    if start or end:
        Time = aliased(NodeHyperdata)

        coocs_query = (coocs_query
                            .join(Time, Time.node_id == Xindex.node_id)
                            .filter(Time.key=="publication_date")
                            )

        if start:
            if not isinstance(start, datetime):
                try:
                    start = datetime.strptime(start, '%Y-%m-%d')
                except:
                    raise TypeError("'start' param expects datetime object or %%Y-%%m-%%d string")

            # the filtering by start limit
            coocs_query = coocs_query.filter(Time.value_utc >= start)

        if end:
            if not isinstance(end, datetime):
                try:
                    end = datetime.strptime(end, '%Y-%m-%d')
                except:
                    raise TypeError("'end' param expects datetime object or %%Y-%%m-%%d string")

            # the filtering by start limit
            coocs_query = coocs_query.filter(Time.value_utc <= end)


    if symmetry_filter:
        # 1 filtre tenant en compte de la symétrie
        #  -> réduit le travail de moitié !!
        #  -> mais récupération sera plus couteuse via des requêtes OR comme:
        #       WHERE ngram1 = mon_ngram OR ngram2 = mon_ngram
        coocs_query = coocs_query.filter(Xindex_ngform_id  < Yindex_ngform_id)


    # 5) OUTPUT FILTERS
    # ------------------
    # threshold
    # £TODO adjust COOC_THRESHOLD a posteriori:
    # ex: sometimes 2 sometimes 4 depending on sparsity
    print("COOCS: filtering pairs under threshold:", threshold)
    coocs_query = coocs_query.having(ucooc >= threshold)


    # 6) EXECUTE QUERY
    # ----------------
    #  => storage in our matrix structure
    matrix = WeightedMatrix(coocs_query.all())
    #                      -------------------

    # fyi
    shape_0 = len({pair[0] for pair in matrix.items})
    shape_1 = len({pair[1] for pair in matrix.items})
    print("COOCS: NEW matrix shape [%ix%i]" % (shape_0, shape_1))


    if just_pass_result:
        return matrix
    else:
        # 5) SAVE
        # --------
        # saving the parameters of the analysis in the Node JSON
        new_hyperdata = { 'corpus'   : corpus.id,
                          'threshold': threshold }

        if overwrite_id:
            # overwrite pre-existing id
            the_cooc = cache.Node[overwrite_id]
            the_cooc.hyperdata = new_hyperdata
            the_cooc.save_hyperdata()
            session.commit()
            the_id = overwrite_id
        else:
            # create the new cooc node
            the_cooc = corpus.add_child(
                            typename  = "COOCCURRENCES",
                            name      = "Coocs (in:%s)" % corpus.name[0:10],
                            hyperdata = new_hyperdata,
                        )
            session.add(the_cooc)
            session.commit()

            the_id = the_cooc.id

        # ==> save all NodeNgramNgram with link to new cooc node id
        matrix.save(the_id)

        return the_id
