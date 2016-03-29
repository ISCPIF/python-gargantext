from gargantext.models     import Node, Ngram, NodeNgram, NodeNgramNgram, \
                                  NodeHyperdata
from gargantext.util.db    import session, aliased, bulk_insert, func

from gargantext.util.lists import WeightedMatrix, UnweightedList, Translations

from sqlalchemy            import desc, asc, or_, and_

#import inspect
import datetime

def do_cooc(corpus=None
         , field1='ngrams', field2='ngrams'
         , mainList_id=None, groupList_id=None
         , coocNode_id=None
         , start=None, end=None
         , n_min=1, n_max=None , limit=1000
         , isMonopartite=True
         , threshold = 3):
    '''
    Compute the cooccurence matrix and save it, returning NodeNgramNgram.node_id
    For the moment list of paramters are not supported because, lists need to
    be merged before.
    corpus           :: Corpus
    
    mainList_id      :: Int
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

#    node_cooc = get_or_create_node(nodetype='Cooccurrence', corpus=corpus
#                                   , name_str="Cooccurrences corpus " \
#                                    + str(corpus.id) + "list_id: " + str(mainList_id)
#                                    #, hyperdata={'field1': field1, 'field2':field2}
#                                   , session=session)

    
    # BEGIN
    # Saving the parameters of the analysis in the Node JSONB hyperdata field
    # ok args, _, _, parameters = inspect.getargvalues(inspect.currentframe())
#    hyperdata = dict()
#    
#    for parameter in parameters.keys():
#        if parameter != 'corpus' and parameter != 'node_cooc':
#            hyperdata[parameter] = parameters[parameter]
#    
#    node_cooc.hyperdata = hyperdata
#
    # For tests only : delete previous cooccurrences
    session.query( NodeNgramNgram ).filter( NodeNgramNgram.node_id == coocNode_id ).delete()
    session.commit()

    
    NodeNgramX = aliased(NodeNgram)
    cooc_score = func.count(NodeNgramX.node_id).label('cooc_score')
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
        StartFormat = aliased(Hyperdata)
        cooc_query = (cooc_query.join(Start, Start.node_id == Node.id)
                                .join(StartFormat, StartFormat.id == Start.hyperdata_id)
                                .filter(StartFormat.name == 'publication_date')
                                .filter(Start.value_datetime >= date_start_utc)
                      )


    if end is not None:
        # TODO : more complexe date format here.
        date_end = datetime.datetime.strptime (str(end), "%Y-%m-%d")
        date_end_utc = date_end.strftime("%Y-%m-%d %H:%M:%S")
        
        End=aliased(NodeHyperdata)
        EndFormat = aliased(Hyperdata)
        cooc_query = (cooc_query.join(End, End.node_id == Node.id)
                                .join(EndFormat, EndFormat.id == End.hyperdata_id)
                                .filter(EndFormat.name == 'publication_date')
                                .filter(End.value_datetime <= date_end_utc)
                      )


    if isMonopartite:
        # Cooc is symetric, take only the main cooccurrences and cut at the limit
        cooc_query = cooc_query.filter(NodeNgramX.ngram_id < NodeNgramY.ngram_id)
    
    cooc_query = cooc_query.having(cooc_score > threshold)
             
    if isMonopartite:
        cooc_query = cooc_query.group_by(NodeNgramX.ngram_id, NodeNgramY.ngram_id)
    else:
        cooc_query = cooc_query.group_by(NodeHyperdataNgram.ngram_id, NodeNgramY.ngram_id)

    cooc_query = cooc_query.order_by(desc('cooc_score'))

    matrix = WeightedMatrix(cooc_query)
    
    # Select according some scores
    
    mainList   = UnweightedList( mainList_id  )
    group_list = Translations  ( groupList_id )
    cooc       = matrix & (mainList * group_list)
    
    cooc.save(coocNode_id)
    return(coocNode_id)