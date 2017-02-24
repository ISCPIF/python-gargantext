"""
COOCS
    (this is the full SQL version, should be more reliable on outerjoin)
"""
from gargantext                import settings
from sqlalchemy                import create_engine, exc
from gargantext.util.lists     import WeightedMatrix
# from gargantext.util.db        import session, aliased, func
from gargantext.util.db_cache  import cache
from gargantext.constants      import DEFAULT_COOC_THRESHOLD, NODETYPES
from gargantext.constants      import INDEXED_HYPERDATA
from gargantext.util.tools     import datetime, convert_to_date

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
      - TODO stoplist_id: stoplist for filtering input ngrams
                     (normally unnecessary if a mainlist is already provided)
      - TODO start, end: provide one or both temporal limits to filter on doc date
                    NB the expected type of parameter value is datetime.datetime
                        (string is also possible but format must follow
                          this convention: "2001-01-01" aka "%Y-%m-%d")
      - symmetry_filter: prevent calculating where ngram1_id  > ngram2_id
      - diagonal_filter: prevent calculating where ngram1_id == ngram2_id
    """

    # 1) prepare direct connection to the DB
    url = 'postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{NAME}'.format(
            **settings.DATABASES['default']
        )

    engine = create_engine( url )
    connection = engine.connect()

    # string vars for our SQL query
    # setting work memory high to improve cache perf.
    final_sql = "set work_mem='1GB'; \n"
    # where
    # final_sql = cooc_sql + select_cooc_sql
    cooc_sql  = ""
    select_cooc_sql    = ""
    # where
    # cooc_sql = cooc_sql + ngram_filter_A_sql + ngram_filter + cooc_filter_sql
    cooc_filter_sql = ""
    ngram_filter_A_sql = ""
    ngram_filter_B_sql = ""

    # 2a) prepare the document selection (normal case)
    cooc_sql += """
    WITH COOC as (
    SELECT
    COALESCE(grA.ngram1_id, wlA.ngram_id) as ngA,
    COALESCE(grB.ngram1_id, wlB.ngram_id) as ngB,
    COUNT(*) AS score
    FROM
    nodes AS n
    --      / \
    --     X   Y
    -- SQL graph for getting the cooccurrences
    """

    # 2b) stating the filters
    cooc_filter_sql = """
        WHERE 
            n.typename  = {nodetype_id}
        AND n.parent_id = {corpus_id}
        GROUP BY 1,2
        --    ==
        -- GROUP BY ngA, ngB
        )
        """.format( nodetype_id = NODETYPES.index('DOCUMENT')
                  , corpus_id=corpus.id
                  )
    
    # 3) taking the cooccurrences of ngram x2
    ngram_filter_A_sql += """
        -- STEP 1: X axis of the matrix
        INNER JOIN nodes_ngrams
                AS ngA  ON ngA.node_id  = n.id
        -- \--> get the occurrences node/ngram of the corpus
        """

    ngram_filter_B_sql += """
        -- STEP 2: Y axi of the matrix
        INNER JOIN nodes_ngrams
                AS ngB  ON ngB.node_id  = n.id
        -- \--> get the occurrences node/ngram of the corpus
        """

    # 3) filter with lists (white or stop)
    # on whiteList
    if on_list_id:
        ngram_filter_A_sql += """
            INNER JOIN nodes_ngrams
                    AS wlA  ON ngA.ngram_id = wlA.ngram_id
                           AND wlA.node_id  = {wla_node_id}
            -- \--> filter with white/main list
            """.format(wla_node_id = on_list_id)

        ngram_filter_B_sql += """
            INNER JOIN nodes_ngrams
                    AS wlB  ON ngB.ngram_id = wlB.ngram_id
                           AND wlB.node_id  = {wlb_node_id}
            -- \--> filter with white/main list
            """.format(wlb_node_id = on_list_id)

    # on stopList
    # TODO NOT TESTED
    if stoplist_id:
        raise("Stoplist not tested yet")
        ngram_filter_A_sql += """
            LEFT JOIN nodes_ngrams
                    AS stA  ON ngA.ngram_id = stA.ngram_id
                           AND stA.node_id  = {sta_node_id}
                           AND stA.ngram_id IS NULL
            -- \--> filter with stop list
            """.format(sta_node_id = stoplist_id)

        ngram_filter_B_sql += """
            LEFT JOIN nodes_ngrams
                    AS stB  ON ngB.ngram_id = stB.ngram_id
                           AND stB.node_id  = {stb_node_id}
                           AND stB.ngram_id IS NULL
            -- \--> filter with white/main list
            """.format(stb_node_id = stoplist_id)


    # 4) prepare the synonyms
    if groupings_id:
        ngram_filter_A_sql += """
        LEFT JOIN  nodes_ngrams_ngrams 
               AS grA  ON wlA.ngram_id = grA.ngram1_id 
                      AND grA.node_id  = {groupings_id}
        -- \--> adding (joining) ngrams that are grouped
        LEFT JOIN  nodes_ngrams
               AS wlAA ON grA.ngram2_id = wlAA.ngram_id
                      AND wlAA.node_id  = wlA.node_id 
        -- \--> adding (joining) ngrams that are not grouped
        --LEFT JOIN  ngrams        AS wlAA ON grA.ngram2_id = wlAA.id
        -- \--> for joining all synonyms even if they are not in the main list (white list)

        """.format(groupings_id = groupings_id)
        
        ngram_filter_B_sql += """
        LEFT JOIN  nodes_ngrams_ngrams
               AS grB  ON wlB.ngram_id = grB.ngram1_id 
                      AND grB.node_id  = {groupings_id}
        -- \--> adding (joining) ngrams that are grouped
        LEFT JOIN  nodes_ngrams 
               AS wlBB ON grB.ngram2_id = wlBB.ngram_id
                      AND wlBB.node_id   = wlB.node_id
        -- \--> adding (joining) ngrams that are not grouped

        -- LEFT JOIN  ngrams        AS wlBB ON grB.ngram2_id = wlBB.id
        -- \--> for joining all synonyms even if they are not in the main list (white list)
        """.format(groupings_id = groupings_id)


    # 5) Buil the main COOC query
    cooc_sql += ngram_filter_A_sql + ngram_filter_B_sql + cooc_filter_sql

    # 6) FILTERS
    select_cooc_sql = """
    SELECT ngA, ngB, score
        FROM COOC    --> from the query above
    """
    # the inclusive threshold filter is always here
    select_cooc_sql += "\n WHERE score >= %i" % threshold

    # don't compute ngram with itself
    # NB: this option is bad for main toolchain
    if diagonal_filter:
        select_cooc_sql += "\n AND ngA != ngB"

    # 1 filtre tenant en compte de la symétrie
    # NB: this option is also bad for main toolchain
    if symmetry_filter:
        select_cooc_sql += "\n AND ngA <= ngB"

    # 7) Building the final query
    final_sql += cooc_sql + select_cooc_sql
    #final_sql += ";\n reset work_mem;"

    # 6) EXECUTE QUERY
    # ----------------
    # debug
    #print(final_sql)

    # executing the SQL statement
    try:
        # suppose the database has been restarted.
        results = connection.execute(final_sql)
        connection.close()
    except exc.DBAPIError as e:
        # an exception is raised, Connection is invalidated.
        if e.connection_invalidated:
            print("Connection was invalidated for ngram_coocs")
        else:
            print(e)

    #  => storage in our matrix structure
    matrix = WeightedMatrix(results)
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
