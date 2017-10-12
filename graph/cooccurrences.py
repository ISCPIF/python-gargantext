from gargantext.models     import Node, Ngram, NodeNgram, NodeNgramNgram, \
                                  NodeHyperdata, HyperdataKey
from gargantext.util.db    import session, aliased, func

from gargantext.util.lists import WeightedMatrix, UnweightedList, Translations

from sqlalchemy            import desc, asc, or_, and_
from datetime              import datetime


def filterMatrix(matrix, mapList_id, groupList_id):
    mapList    = UnweightedList( mapList_id  )
    group_list = Translations  ( groupList_id )
    cooc       = matrix & (mapList * group_list)
    return cooc


def countCooccurrences( corpus_id=None      , cooc_id=None
                      , field1='ngrams'     , field2='ngrams'
                      , start=None          , end=None
                      , mapList_id=None     , groupList_id=None
                      , distance=None       , bridgeness=None
                      , n_min=1, n_max=None , limit=1000
                      , isMonopartite=True  , threshold = 3
                      , save_on_db= True    , reset=True
                      ):
    '''
    Compute the cooccurence matrix and save it, returning NodeNgramNgram.node_id
    For the moment list of parameters are not supported because, lists need to
    be merged before.
    corpus           :: Corpus

    mapList_id       :: Int
    groupList_id     :: Int

    start :: TimeStamp -- example: '2010-05-30 02:00:00+02'
    end   :: TimeStamp
    limit :: Int

    '''
    # FIXME remove the lines below after factorization of parameters
    parameters = dict()
    parameters['field1'] = field1
    parameters['field2'] = field2

    # Get corpus as Python object
    corpus = session.query(Node).filter(Node.id==corpus_id).first()

    # Get node of the Graph
    if not cooc_id:

        cooc_id  = ( session.query( Node.id )
                                .filter( Node.typename  == "COOCCURRENCES"
                                       , Node.name      == "GRAPH EXPLORER"
                                       , Node.parent_id == corpus.id
                                       )
                                .first()
                        )
        if not cooc_id:
            coocNode = corpus.add_child(
            typename  = "COOCCURRENCES",
            name = "GRAPH (in corpus %s)" % corpus.id
            )

            session.add(coocNode)
            session.commit()
            cooc_id = coocNode.id
        else :
            cooc_id = int(cooc_id[0])

    # when cooc_id preexisted, but we want to continue  (reset = True)
    #    (to give new contents to this cooc_id)
    elif reset:
        print("GRAPH #%s ... Counting new cooccurrences data." % cooc_id)
        session.query( NodeNgramNgram ).filter( NodeNgramNgram.node_id == cooc_id ).delete()
        session.commit()

    # when cooc_id preexisted and we just want to load it (reset = False)
    else:
        print("GRAPH #%s ... Loading cooccurrences computed already." % cooc_id)
        cooc = session.query( NodeNgramNgram.ngram1_id, NodeNgramNgram.ngram2_id, NodeNgramNgram.weight ).filter( NodeNgramNgram.node_id == cooc_id ).all()
        return(int(cooc_id),WeightedMatrix(cooc))



    NodeNgramX = aliased(NodeNgram)

    # Simple Cooccurrences
    cooc_score = func.count(NodeNgramX.node_id).label('cooc_score')

    # A kind of Euclidean distance cooccurrences
    #cooc_score = func.sqrt(func.sum(NodeNgramX.weight * NodeNgramY.weight)).label('cooc_score')

    if isMonopartite :
        NodeNgramY = aliased(NodeNgram)

        cooc_query = (session.query( NodeNgramX.ngram_id
                                   , NodeNgramY.ngram_id
                                   , cooc_score
                                   )
                             .join( Node
                                  , Node.id == NodeNgramX.node_id
                                  )
                             .join( NodeNgramY
                                  , NodeNgramY.node_id == Node.id
                                  )
                             .filter( Node.parent_id==corpus.id
                                    , Node.typename=="DOCUMENT"
                                    )
                     )
    else :
        NodeNgramY = aliased(NodeNgram)

        cooc_query = (session.query( NodeHyperdataNgram.ngram_id
                                   , NodeNgramY.ngram_id
                                   , cooc_score
                                   )
                             .join( Node
                                  , Node.id == NodeHyperdataNgram.node_id
                                  )
                             .join( NodeNgramY
                                  , NodeNgramY.node_id == Node.id
                                  )
                             .join( Hyperdata
                                  , Hyperdata.id == NodeHyperdataNgram.hyperdata_id
                                  )
                             .filter( Node.parent_id == corpus.id
                                    , Node.typename == "DOCUMENT"
                                    )
                             .filter( Hyperdata.name == field1 )
                     )

    # Size of the ngrams between n_min and n_max
    if n_min is not None or n_max is not None:
        if isMonopartite:
            NgramX = aliased(Ngram)
            cooc_query = cooc_query.join ( NgramX
                                         , NgramX.id == NodeNgramX.ngram_id
                                         )

        NgramY = aliased(Ngram)
        cooc_query = cooc_query.join ( NgramY
                                     , NgramY.id == NodeNgramY.ngram_id
                                     )

    if n_min is not None:
        cooc_query = (cooc_query
             .filter(NgramY.n >= n_min)
            )
        if isMonopartite:
            cooc_query = cooc_query.filter(NgramX.n >= n_min)

    if n_max is not None:
        cooc_query = (cooc_query
             .filter(NgramY.n >= n_min)
            )
        if isMonopartite:
            cooc_query = cooc_query.filter(NgramX.n >= n_min)

    # Cooc between the dates start and end
    if start is not None:
        #date_start = datetime.datetime.strptime ("2001-2-3 10:11:12", "%Y-%m-%d %H:%M:%S")
        # TODO : more precise date format here (day is smaller grain actually).
        date_start = datetime.strptime (str(start), "%Y-%m-%d")
        date_start_utc = date_start.strftime("%Y-%m-%d %H:%M:%S")

        Start=aliased(NodeHyperdata)
        cooc_query = (cooc_query.join( Start
                                     , Start.node_id == Node.id
                                     )
                                .filter( Start.key == 'publication_date')
                                .filter( Start.value_utc >= date_start_utc)
                      )

        parameters['start'] = date_start_utc


    if end is not None:
        # TODO : more precise date format here (day is smaller grain actually).
        date_end = datetime.strptime (str(end), "%Y-%m-%d")
        date_end_utc = date_end.strftime("%Y-%m-%d %H:%M:%S")

        End=aliased(NodeHyperdata)

        cooc_query = (cooc_query.join( End
                                     , End.node_id == Node.id
                                     )
                                .filter( End.key == 'publication_date')
                                .filter( End.value_utc <= date_end_utc )
                      )

        parameters['end'] = date_end_utc

    if isMonopartite:
        # Cooc is symetric, take only the main cooccurrences and cut at the limit
        cooc_query = cooc_query.filter(NodeNgramX.ngram_id < NodeNgramY.ngram_id)

    cooc_query = cooc_query.having(cooc_score >= threshold)

    if isMonopartite:
        cooc_query = cooc_query.group_by(NodeNgramX.ngram_id, NodeNgramY.ngram_id)
    else:
        cooc_query = cooc_query.group_by(NodeHyperdataNgram.ngram_id, NodeNgramY.ngram_id)

    # Order according some scores
    # If ordering is really needed, use Ordered Index (faster)
    #cooc_query = cooc_query.order_by(desc('cooc_score'))

    matrix = WeightedMatrix(cooc_query)

    print("GRAPH #%s Filtering the matrix with Map and Group Lists." % cooc_id)
    cooc = filterMatrix(matrix, mapList_id, groupList_id)

    parameters['MapList_id']   = str(mapList_id)
    parameters['GroupList_id'] = str(groupList_id)

    # TODO factorize savings on db
    if save_on_db:
        # Saving the cooccurrences
        cooc.save(cooc_id)
        print("GRAPH #%s ... Node Cooccurrence Matrix saved" % cooc_id)

        # Saving the parameters
        print("GRAPH #%s ... Parameters saved in Node." % cooc_id)
        coocNode = session.query(Node).filter(Node.id==cooc_id).first()

        coocNode.hyperdata["parameters"] = dict()
        coocNode.hyperdata["parameters"] = parameters
        coocNode.save_hyperdata()
        session.commit()

        #data = cooc2graph(coocNode.id, cooc, distance=distance, bridgeness=bridgeness)
    else:
        return cooc

    return(coocNode.id, cooc)
