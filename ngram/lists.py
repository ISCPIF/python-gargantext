from admin.utils import PrintException

from gargantext_web.db import NodeNgram, get_session
from gargantext_web.db import *
from parsing.corpustools import *

import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased


def listIds(typeList=None, user_id=None, corpus_id=None):
    '''
    nodeList : get or create NodeList.
    nodeList :: Integer -> Integer -> String -> [Node]
    user_id   :: Integer
    corpus_id :: Integer
    typeList  :: String, Type of the Node that should be created
    [Node]      :: List of Int, returned or created by the function
    '''
    
    session = get_session()

    if typeList is None:
        typeList = 'MiamList'

    if corpus_id is not None and user_id is not None:

        # Nodes are either in root_list or user_list
        root_list = ['Stem', 'Lem']
        user_list   = ['MiamList', 'StopList', 'MapList', 'Group']

        if typeList in user_list:
            nodes = session.query(Node).filter(
                                    Node.user_id == user_id,
                                    Node.parent_id==corpus_id,
                                    Node.type_id == cache.NodeType[typeList].id
                                    ).order_by(desc(Node.id)).all()
        elif typeList in root_list:
            nodes = session.query(Node).filter(
                                    Node.type_id == cache.NodeType[typeList].id
                                    ).order_by(desc(Node.id)).all()
        else:
            raise Exception("typeList %s not supported yet" % typeList)

        if nodes == []:
            node = Node(user_id = user_id,
                        parent_id=corpus_id,
                        type_id=cache.NodeType[typeList].id,
                        name="First default Node " + str(typeList))

            session.add(node)
            session.commit()
            return([(node.id, node.name),])
        else:
            return([(node.id, node.name) for node in nodes])

    else:
        raise Exception("Usage (Warning): Need corpus_id and user_id")
    
    session.remove()


# Some functions to manage ngrams according to the lists

def listNgramIds(list_id=None, typeList=None,
                 corpus_id=None, doc_id=None, user_id=None):
    '''
    listNgramsIds :: Int | String, Int, Int, Int -> [(Int, String, Int)]
    return has types: [(ngram_id, ngram_terms, occurrences)]

    Return the list of tuples of
    ngram_id and its occurrences according to node_id level.

    list_id   : Node.id of the list expected
    typeList  : needed if no list_id, use typeList such as 'MiamList' or 'StopList'
    corpus_id : needed to get list_id
    doc_id    : to get specific ngrams related to a document with Node.id=doc_id
    user_id   : needed to create list if it does not exist
    '''
    
    session = get_session()

    if typeList is None:
        typeList = ['MiamList', 'StopList']
    elif isinstance(typeList, string):
        typeList = [typeList]

    if list_id is None and corpus_id is None:
        raise Exception('Need a listId or corpusId to query')

    if user_id is None:
        raise Exception("Need a user_id to create list if needed")

    # iterate over every list in a corpus
    try:
        allLists = []
        for aType in typeList:
            allLists += listIds(user_id=user_id, corpus_id=corpus_id, typeList=aType)
    except Exception as exc:
        PrintException()
        raise exc

    ListNgram = aliased(NodeNgram)
    or_args = [ListNgram.node_id == l[0] for l in allLists]
    query = (session.query(Ngram.id, Ngram.terms, func.sum(ListNgram.weight), ListNgram.node_id)
            .join(ListNgram, ListNgram.ngram_id == Ngram.id)
            .filter(or_(*or_args))
            .group_by(Ngram.id, ListNgram.node_id)
            )

    if doc_id is not None:
        Doc      = aliased(Node)
        DocNgram = aliased(NodeNgram)
        query = (query
                     .join(DocNgram, DocNgram.ngram_id == Ngram.id)
                     .join(Doc, Doc.id == doc_id)
                     .filter(DocNgram.node_id == Doc.id)
                )

    return(query.all())
    
    session.remove()

def ngramList(do, list_id, ngram_ids=None) :
    '''
    ngramList :: ([Int], Int, String) -> Bool
    Do (delete | add) [ngram_id] (from | to) the list_id

    options:
        do        = String : action 'del' or 'add'
        ngram_id  = [Int]  : list of Ngrams id (Ngrams.id)
        list_id   = Int    : list id (Node.id)
    '''
    session = get_session()
    
    results = []

    if do == 'create':
        terms = copy(ngram_ids)
        ngram_ids = []
        for ngram_term in terms:
            # TODO set the language correctly
            ngram = Ngram.objects.get_or_create(terms=ngram_term, n=len(terms.split()),
                                                language='en')
            ngram_ids += [ngram.id]

    for ngram_id in ngram_ids:
        # Fetch the ngram from database
        ngram = session.query(Ngram.id, Ngram.terms, func.count()).filter(Ngram.id == ngram_id).first()
        # Need to be optimized with list of ids
        node_ngram = (session.query(NodeNgram)
                .filter(NodeNgram.ngram_id == ngram_id)
                .filter(NodeNgram.node_id  == list_id)
                .first()
                )
        # create NodeNgram if does not exists
        if node_ngram is None :
            node_ngram = NodeNgram(node_id = list_id, ngram_id=ngram_id,
                                    weight=1)
        if do == 'add' :
            session.add(node_ngram)
            results += [ngram]

        elif do == 'del' :
            session.delete(node_ngram)

    session.commit()
    return(results)
    session.remove()

# Some functions to manage automatically the lists
def doStopList(user_id=None, corpus_id=None, stop_id=None, reset=False, limit=None):
    '''
    Compute automatically the stopList and returns its Node.id
    Algo: TODO tfidf according type of corpora
    '''

    if stop_id is None:
        stop_id = listNgramIds(user_id=user_id,
                            corpus_id=corpus_id,
                            typeList='StopList')[0]
    # according to type of corpus, choose the right default stopList

def ngrams2miam(user_id=None, corpus_id=None):
    '''
    Create a Miam List only
    '''
    session = get_session()

    miam_id = listIds(typeList='MiamList', user_id=user_id, corpus_id=corpus_id)[0][0]
    print(miam_id)

    query = (session.query(
                literal_column(str(miam_id)).label("node_id"),
                Ngram.id,
                func.count(),
                )
                .select_from(Ngram)
                .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                .join(Node, NodeNgram.node_id == Node.id)
                .filter(Node.parent_id == corpus_id)
                .filter(Node.type_id == cache.NodeType['Document'].id)

                .group_by(Ngram.id)
                #.limit(10)
                .all()
                )
    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], query)
    session.remove()

from gargantext_web.db import get_or_create_node
from analysis.lists import Translations, UnweightedList

def ngrams2miamBis(corpus):
    '''
    Create a Miam List only
    '''

    miam_id = get_or_create_node(corpus=corpus, nodetype='MiamList')
    stop_id = get_or_create_node(corpus=corpus,nodetype='StopList')
    
    session = get_session()

    query = (session.query(
                literal_column(str(miam_id)).label("node_id"),
                Ngram.id,
                func.count(),
                )
                .select_from(Ngram)
                .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                .join(Node, NodeNgram.node_id == Node.id)
                .filter(Node.parent_id == corpus_id)
                .filter(Node.type_id == cache.NodeType['Document'].id)

                .group_by(Ngram.id)
                #.limit(10)
                .all()
                )
    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], query)
    session.remove()

def doList(
        type_list='MiamList',
        user_id=None, corpus_id=None,
        miam_id=None, stop_id=None, main_id=None,
        lem_id=None, stem_id=None, cvalue_id=None, group_id=None,
        reset=True, limit=None
    ):
    '''
    Compute the miamList and returns its Node.id
    miamList = allList - stopList
    where:
        allList  = all Ngrams
        stopList = all Stop Ngrams

    OR

    Compute the mainList : main Forms
    mainList = miamList - (stem|lem|group|cvalue) List
    where:
        group   = Words grouped manually by user
        stem    = equivalent Words which are stemmed (but the main form)
        lem     = equivalent Words which are lemmatized (but the main form)
        cvalue  = equivalent N-Words according to C-Value (but the main form)
    '''
    session = get_session()

    if type_list not in ['MiamList', 'MainList']:
        raise Exception("Type List (%s) not supported, try: \'MiamList\' or \'MainList\'" % type_list)

    try:
        list_dict = {
            'miam' : { 'type' : 'MiamList', 'id' : miam_id},
            'stop' : { 'type' : 'StopList', 'id' : stop_id},
                    }

        if 'main' == type_list:
            list_dict.update(
            {
                'main' : { 'type' : 'MainList', 'id' : main_id},
                'stem' : { 'type' : 'Stem', 'id' : stem_id},
                #'lem' : { 'type' : 'LemList', 'id' : lem_id},
                #'group' : { 'type' : 'Group', 'id' : group_id},
            }
            )

        for list_ in list_dict.keys():
            if  list_dict[list_]['id'] is None:
                list_dict[list_]['id'] = listNgramIds(user_id=user_id,
                                        corpus_id=corpus_id,
                                        typeList=list_dict[list_]['type'])[0][0]
        # Delete previous List ?
        # By default, miamList is computed each time
        if reset is True:
            session.query(NodeNgram).filter(
                    NodeNgram.node_id == list_dict[type_list]['id']
                    ).delete()

    except:
        PrintException()

    stopNgram = aliased(NodeNgram)

    if type_list == 'MiamList' :
        query = (session.query(
                literal_column(str(list_dict['miam']['id'])).label("node_id"),
                Ngram.id,
                func.count(),
                )
                .select_from(Ngram)
                .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                .join(Node, NodeNgram.node_id == Node.id)
                .outerjoin(stopNgram,
                            and_(stopNgram.ngram_id == Ngram.id,
                                stopNgram.node_id == list_dict['stop']['id']))

                .filter(Node.parent_id == corpus_id)
                .filter(Node.type_id == cache.NodeType['Document'].id)
                .filter(stopNgram.id == None )

                .group_by(Ngram.id)
                )

    elif type_list == 'MainList' :
        # Query to get Ngrams for main list
        query = (session.query(
                literal_column(str(list_dict['main']['id'])).label("node_id"),
                Ngram.id,
                func.count(),
                )
                .select_from(Ngram)
                .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)

                .filter(NodeNgram.node_id == list_dict['miam']['id'])
                )

        if stem_id is not None:
        # Query with Stems Result need to be checked before prod
            snn1   = aliased(NodeNgramNgram)
            snn2   = aliased(NodeNgramNgram)
            query = (query.outerjoin(snn1,
                          and_(snn1.ngramx_id == Ngram.id,
                               snn1.node_id   == list_dict['stem']['id']
                              )
                                    )
                          .outerjoin(snn2,
                          and_(snn1.ngramy_id == snn2.ngramy_id,
                               snn2.node_id   == list_dict['stem']['id'],
                               snn1.ngramx_id < snn2.ngramx_id
                              )
                                    )

                    .filter(snn2.id == None)
                    )
    # Specific group by:
    if stem_id is not None:
        query = query.group_by(Ngram.id, snn1.ngramx_id)
    else:
        query = query.group_by(Ngram.id)

    # here add filter for size of the ngram

    # Order result by occurrences descending
    query = query.order_by(desc(func.count()))
    # Adding specific filters
    if limit is not None:
        query = query.limit(limit)
    else:
        query = query.all()

    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], query)

    return(list_dict[type_list]['id'])
    session.remove()


