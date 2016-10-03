"""
COOCS
    (this is the full SQL version, should be more reliable on outerjoin)
"""
from gargantext                import settings
from sqlalchemy                import create_engine
from gargantext.util.lists     import WeightedMatrix
# from gargantext.util.db        import session, aliased, func
from gargantext.util.db_cache  import cache
from gargantext.constants      import DEFAULT_COOC_THRESHOLD
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
      - stoplist_id: stoplist for filtering input ngrams
                     (normally unnecessary if a mainlist is already provided)
      - start, end: provide one or both temporal limits to filter on doc date
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
    sql_statement     = ""
    doc_idx_statement = ""

    # 2a) prepare the document selection (normal case)
    doc_idx_statement = """
    SELECT node_id, ngram_id
    FROM nodes_ngrams
    JOIN nodes
        ON node_id = nodes.id
    WHERE nodes.parent_id = {corpus_id}
    AND nodes.typename = 4
    """.format(corpus_id=corpus.id)


    # 2b) same if document filters
    if start or end:
        date_type_id = INDEXED_HYPERDATA['publication_date']['id']

        doc_idx_statement = """
        SELECT node_id, ngram_id
        FROM nodes_ngrams
        JOIN nodes
            ON node_id = nodes.id
        -- preparing for date filter (1/2)
        JOIN nodes_hyperdata
            ON nodes_hyperdata.node_id = nodes_ngrams.node_id
        WHERE nodes.parent_id = {corpus_id}
        AND nodes.typename = 4

        -- preparing for date filter (2/2)
        AND nodes_hyperdata.key = {date_type_id}
        """.format(corpus_id=corpus.id, date_type_id = date_type_id)

        if start:
            if not isinstance(start, datetime):
                try:
                    start = datetime.strptime(start, '%Y-%m-%d')
                except:
                    raise TypeError("'start' param expects datetime object or %%Y-%%m-%%d string")

            # datetime object ~> date db formatted filter (2013-09-16 00:00:00+02)
            start_filter = "AND nodes_hyperdata.value_utc >= %s::date" % start.strftime('%Y-%m-%d %H:%M:%S%z')

            # the filtering by start limit
            doc_idx_statement += "\n" + start_filter

        if end:
            if not isinstance(end, datetime):
                try:
                    end = datetime.strptime(end, '%Y-%m-%d')
                except:
                    raise TypeError("'end' param expects datetime object or %%Y-%%m-%%d string")

            # datetime object ~> date db formatted filter
            end_filter = "AND nodes_hyperdata.value_utc <= %s::date" % end.strftime('%Y-%m-%d %H:%M:%S%z')

            # the filtering by end limit
            doc_idx_statement += "\n" + end_filter

    # 4) prepare the synonyms
    if groupings_id:
        syn_statement = """
         SELECT * FROM nodes_ngrams_ngrams
         WHERE node_id = {groupings_id}
        """.format(groupings_id = groupings_id)


    # 5a) MAIN DB QUERY SKELETON (no groupings) --------------------------------
    if not groupings_id:
        sql_statement = """
        SELECT cooc.*
        FROM (
         SELECT idxA.ngram_id AS ngA,
                idxB.ngram_id AS ngB,
          count((idxA.ngram_id,
                 idxB.ngram_id)) AS cwei
          -- read doc index x 2
          FROM ({doc_idx}) AS idxA
          JOIN ({doc_idx}) AS idxB
          -- cooc <=> in same doc node
          ON idxA.node_id = idxB.node_id

          GROUP BY ((idxA.ngram_id,idxB.ngram_id))
        ) AS cooc
        """.format(doc_idx = doc_idx_statement)
    # --------------------------------------------------------------------------

    # 5b) MAIN DB QUERY SKELETON (with groupings)
    # groupings: we use additional Translation (synonyms) for ngA and ngB
    else:
        sql_statement = """
        SELECT cooc.*
        FROM (
         SELECT COALESCE(synA.ngram1_id, idxA.ngram_id) AS ngA,
                COALESCE(synB.ngram1_id, idxB.ngram_id) AS ngB,
          count((COALESCE(synA.ngram1_id, idxA.ngram_id),
                COALESCE(synB.ngram1_id, idxB.ngram_id))) AS cwei
          -- read doc index x 2
          FROM ({doc_idx}) AS idxA
          JOIN ({doc_idx}) AS idxB
          -- cooc <=> in same doc node
          ON idxA.node_id = idxB.node_id

          -- when idxA.ngram_id is a subform
          LEFT JOIN ({synonyms}) as synA
          ON synA.ngram2_id = idxA.ngram_id
          -- when idxB.ngram_id is a subform
          LEFT JOIN ({synonyms}) as synB
          ON synB.ngram2_id = idxB.ngram_id

          GROUP BY (COALESCE(synA.ngram1_id, idxA.ngram_id),
                    COALESCE(synB.ngram1_id, idxB.ngram_id))
        ) AS cooc
        """.format(doc_idx = doc_idx_statement,
                   synonyms = syn_statement)


    # 6) prepare 2 x node_ngrams alias if whitelist
    if on_list_id:
        sql_statement +="""
        JOIN nodes_ngrams AS whitelistA
          ON whitelistA.ngram_id = cooc.ngA

        JOIN nodes_ngrams AS whitelistB
          ON whitelistB.ngram_id = cooc.ngB
         """

    if stoplist_id:
        pass
        # TODO reverse join

    # 7) FILTERS

    # the inclusive threshold filter is always here
    sql_statement += "\n WHERE cooc.cwei >= %i" % threshold

    # the optional whitelist perimeters
    if on_list_id:
        sql_statement += "\n AND whitelistA.node_id = %i" % on_list_id
        sql_statement += "\n AND whitelistB.node_id = %i" % on_list_id

    # don't compute ngram with itself
    # NB: this option is bad for main toolchain
    if diagonal_filter:
        sql_statement += "\n AND ngA != ngB"

    # 1 filtre tenant en compte de la symétrie
    # NB: this option is also bad for main toolchain
    if symmetry_filter:
        sql_statement += "\n AND ngA <= ngB"



    # 6) EXECUTE QUERY
    # ----------------
    # executing the SQL statement
    results = connection.execute(sql_statement)

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
