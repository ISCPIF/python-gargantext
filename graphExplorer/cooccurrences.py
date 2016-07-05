from gargantext.models     import Node, Ngram, NodeNgram, NodeNgramNgram, \
                                  NodeHyperdata, HyperdataKey
from gargantext.util.db    import session, aliased, bulk_insert, func

from gargantext.util.lists import WeightedMatrix, UnweightedList, Translations

from sqlalchemy            import desc, asc, or_, and_

#import inspect
import datetime


def filterMatrix(matrix, mapList_id, groupList_id):
    mapList   = UnweightedList( mapList_id  )
    group_list = Translations  ( groupList_id )
    cooc       = matrix & (mapList * group_list)
    return cooc


def countCooccurrences( corpus=None         , test= False
                      , field1='ngrams'     , field2='ngrams'
                      , start=None          , end=None
                      , mapList_id=None     , groupList_id=None
                      , n_min=1, n_max=None , limit=1000
                      , coocNode_id=None    , reset=True
                      , isMonopartite=True  , threshold = 3
                      , save_on_db= False,  # just return the WeightedMatrix,
                                                 #    (don't write to DB)
                      ):
    '''
    Compute the cooccurence matrix and save it, returning NodeNgramNgram.node_id
    For the moment list of paramters are not supported because, lists need to
    be merged before.
    corpus           :: Corpus

    mapList_id       :: Int
    groupList_id     :: Int

    For the moment, start and end are simple, only year is implemented yet
    start :: TimeStamp -- example: '2010-05-30 02:00:00+02'
    end   :: TimeStamp
    limit :: Int

    '''
    # TODO : add hyperdata here

    # Security test
    field1,field2 = str(field1), str(field2)

    # Get node
    if not coocNode_id:
        coocNode_id0  = ( session.query( Node.id )
                                .filter( Node.typename  == "COOCCURRENCES"
                                       , Node.name      == "GRAPH EXPLORER"
                                       , Node.parent_id == corpus.id
                                       )
                                .first()
                        )
        if not coocNode_id:
            coocNode = corpus.add_child(
            typename  = "COOCCURRENCES",
            name = "GRAPH EXPLORER COOC (in:%s)" % corpus.id
            )

            session.add(coocNode)
            session.commit()
            coocNode_id = coocNode.id
        else :
            coocNode_id = coocNode_id[0]

    if reset == True :
        session.query( NodeNgramNgram ).filter( NodeNgramNgram.node_id == coocNode_id ).delete()
        session.commit()


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
        # TODO : more complexe date format here.
        date_start = datetime.datetime.strptime (str(start), "%Y-%m-%d")
        date_start_utc = date_start.strftime("%Y-%m-%d %H:%M:%S")

        Start=aliased(NodeHyperdata)
        cooc_query = (cooc_query.join( Start
                                     , Start.node_id == Node.id
                                     )
                                .filter( Start.key == 'publication_date')
                                .filter( Start.value_utc >= date_start_utc)
                      )


    if end is not None:
        # TODO : more complexe date format here.
        date_end = datetime.datetime.strptime (str(end), "%Y-%m-%d")
        date_end_utc = date_end.strftime("%Y-%m-%d %H:%M:%S")

        End=aliased(NodeHyperdata)

        cooc_query = (cooc_query.join( End
                                     , End.node_id == Node.id
                                     )
                                .filter( End.key == 'publication_date')
                                .filter( End.value_utc <= date_end_utc )
                      )


    if isMonopartite:
        # Cooc is symetric, take only the main cooccurrences and cut at the limit
        cooc_query = cooc_query.filter(NodeNgramX.ngram_id < NodeNgramY.ngram_id)

    cooc_query = cooc_query.having(cooc_score > threshold)

    if isMonopartite:
        cooc_query = cooc_query.group_by(NodeNgramX.ngram_id, NodeNgramY.ngram_id)
    else:
        cooc_query = cooc_query.group_by(NodeHyperdataNgram.ngram_id, NodeNgramY.ngram_id)

    # Order according some scores
    # If ordering is really needed, use Ordered Index (faster)
    #cooc_query = cooc_query.order_by(desc('cooc_score'))

    matrix = WeightedMatrix(cooc_query)
    cooc = filterMatrix(matrix, mapList_id, groupList_id)

    if save_on_db:
        cooc.save(coocNode_id)
        print("Cooccurrence Matrix saved")
    
    return cooc
