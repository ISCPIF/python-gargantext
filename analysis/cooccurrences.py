from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func

from gargantext_web.db import Node, Ngram, NodeNgram, NodeNgramNgram, \
        NodeNodeNgram, NodeHyperdata, Hyperdata
from gargantext_web.db import session, cache, get_or_create_node, bulk_insert
from analysis.lists import WeightedMatrix, UnweightedList, Translations

def cooc(corpus=None
         , field_X=None, field_Y=None
         , miam_id=None, stop_id=None, group_id=None
         , cvalue_id=None
         , n_min=2, n_max=None
         , start=None, end=None
         , limit=1000):
    '''
    Compute the cooccurence matrix and save it, returning NodeNgramNgram.node_id
    For the moment list of paramters are not supported because, lists need to
    be merged before.
    corpus :: Corpus
    cvalue_id :: Int
    miam_id :: Int
    stop_id :: Int
    group_id :: Int

    For the moment, start and ens are simple, only year is implemented yet
    start :: TimeStamp -- example: '2010-05-30 02:00:00+02'
    end   :: TimeStamp
    limit :: Int

    '''
    node_cooc = get_or_create_node(nodetype='Cooccurrence', corpus=corpus
                                   , name_str="Cooccurrences corpus " + str(corpus.id) + "list_id: " + str(miam_id)
                                   )

# TODO : save parameters in Node
#    args, _, _, parameters = inspect.getargvalues(inspect.currentframe())
#    print(parameters)
#    for parameter in parameters.keys():
#        print(parameters[parameter])
#        node_cooc.hyperdata[parameter] = parameters[parameter]
#
#    session.add(node_cooc)
#    session.commit()
#    print(node_cooc.hyperdata)

    session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==node_cooc.id).delete()
    session.commit()

    NodeNgramX = aliased(NodeNgram)
    NodeNgramY = aliased(NodeNgram)

    doc_id = cache.NodeType['Document'].id

    cooc_query = (session.query(NodeNgramX.ngram_id, NodeNgramY.ngram_id, func.count())
             .join(Node, Node.id == NodeNgramX.node_id)
             .join(NodeNgramY, NodeNgramY.node_id == Node.id)
             .filter(Node.parent_id==corpus.id, Node.type_id==doc_id)
                )
    
# Size of the ngrams between n_min and n_max
    if n_min is not None or n_max is not None:
        NgramX = aliased(Ngram)
        NgramY = aliased(Ngram)

        cooc_query = (cooc_query
             .join(NgramX, NgramX.id == NodeNgramX.ngram_id)
             .join(NgramY, NgramY.id == NodeNgramY.ngram_id)
            )

    if n_min is not None:
        cooc_query = (cooc_query
             .filter(NgramX.n >= n_min)
             .filter(NgramY.n >= n_min)
            )

    if n_max is not None:
        cooc_query = (cooc_query
             .filter(NgramX.n >= n_min)
             .filter(NgramY.n >= n_min)
            )

# Cooc between the dates start and end
    if start is not None:
        Start=aliased(NodeHyperdata)
        StartFormat = aliased(Hyperdata)
        cooc_query = (cooc_query.join(Start, Start.node_id == Node.id)
                                .join(StartFormat, StartFormat.id == Start.hyperdata_id)
                                .filter(StartFormat.name == 'datetime')
                                .filter(Start.value_datetime >= start)
                      )


    if end is not None:
        End=aliased(NodeHyperdata)
        EndFormat = aliased(Hyperdata)
        cooc_query = (cooc_query.join(End, End.node_id == Node.id)
                                .join(EndFormat, EndFormat.id == End.hyperdata_id)
                                .filter(EndFormat.name == 'datetime')
                                .filter(End.value_datetime <= end)
                      )


# Cooc is symetric, take only the main cooccurrences and cut at the limit
    cooc_query = (cooc_query.filter(Node.parent_id == corpus.id, Node.type_id == doc_id)
             .filter(NodeNgramX.ngram_id < NodeNgramY.ngram_id)

             .group_by(NodeNgramX.ngram_id, NodeNgramY.ngram_id)
             .order_by(desc(func.count()))

             .limit(limit)
             )

    matrix = WeightedMatrix(cooc_query)
    #print(matrix)

# Select according some scores
    if cvalue_id is not None :
        #miam = get_or_create_node(nodetype='Cvalue', corpus=corpus)
        cvalue_list = UnweightedList(session.query(NodeNodeNgram.ngram_id)
                                   .filter(NodeNodeNgram.nodex_id == cvalue_id).all()
                                   )

    if miam_id is not None :
        #miam = get_or_create_node(nodetype='Cvalue', corpus=corpus)
        miam_list = UnweightedList(miam_id)

    if stop_id is not None :
        #stop = get_or_create_node(nodetype='StopList', corpus=corpus)
        stop_list = UnweightedList(stop_id)

    if group_id is not None :
        group_list = Translations(group_id)

    if miam_id is not None and stop_id is None and group_id is None :
        cooc = matrix & miam_list
    elif miam_id is not None and stop_id is not None and group_id is None :
        cooc = matrix & (miam_list - stop_list)
    elif miam_id is not None and stop_id is not None and group_id is not None :
        cooc = matrix & (miam_list * group_list - stop_list)
    elif miam_id is not None and stop_id is None and group_id is not None :
        cooc = matrix & (miam_list * group_list)
    else :
        cooc = matrix
    
    cooc.save(node_cooc.id)
    return(node_cooc.id)
