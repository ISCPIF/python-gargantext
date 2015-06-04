import sys
from admin.utils import PrintException

from gargantext_web.db import NodeNgram
from gargantext_web.db import *
from parsing.corpustools import *

import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

# from gargantext_web.db import Node, get_cursor

def nodeList(user_id=None, corpus_id=None, typeList='MiamList'):
    '''
    nodeList : get or create NodeList.
    nodeList :: Integer -> Integer -> String -> [Node]
    user_id   :: Integer
    corpus_id :: Integer
    typeList  :: String, Type of the Node that should be created
    [Node]      :: List of Int, returned or created by the function
    '''
    if corpus_id is not None and user_id is not None:

        # Nodes are either in root_list or user_list
        root_list = ['Stem', 'Lem']
        user_list   = ['MiamList', 'StopList', 'MainList']

        if typeList in user_list:
            nodes = session.query(Node).filter(
                                    Node.user_id == user_id,
                                    Node.parent_id==corpus_id,
                                    Node.type_id == cache.NodeType[typeList].id
                                    ).all()
        elif typeList in root_list:
            nodes = session.query(Node).filter(
                                    Node.type_id == cache.NodeType[typeList].id
                                    ).all()
        else:
            print('typeList not supported yet')
            sys.exit(0)


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
        print("Usage (Warning): Need corpus_id and user_id")

def stopList(user_id=None, corpus_id=None,
            stop_id=None,
            reset=False, limit=None
             ):
    '''
    Compute the stopList and returns its Node.id
    '''

    if stop_id is None:
        stop_id = nodeList(user_id=user_id,
                            corpus_id=corpus_id,
                            typeList='StopList')
    # according to type of corpus, choose the right default stopList

def doList(
            type_list='miam',
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

    if type_list not in ['miam', 'main']:
        print('Type List supported: \'miam\' or \'main\'')
        sys.exit(0)

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
                list_dict[list_]['id'] = nodeList(user_id=user_id,
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

    stopNgram        = aliased(NodeNgram)


    if 'miam' == type_list:
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

    elif 'main' == type_list:
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

