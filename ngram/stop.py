import re
from admin.utils import PrintException

from gargantext_web.db import Node, Ngram, NodeNgram,NodeNodeNgram
from gargantext_web.db import cache, session, get_or_create_node, bulk_insert

import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

from ngram.tools import insert_ngrams
from analysis.lists import WeightedList, UnweightedList

def importStopList(node,filename,language='fr'):
    with open(filename, "r") as f:
        stop_list = f.read().splitlines()
    
    stop_words = set(stop_list)
    stop_ids = insert_ngrams([(word, len(word.split(' '))) for word in stop_words])

    stop_node = get_or_create_node(nodetype='StopList', corpus=node)
    stop_node.language_id = cache.Language[language].id
    session.add(stop_node)
    session.commit()
    
    size = len(list(stop_words))

    data = zip(
        [stop_node.id for i in range(0,size)]
        , [stop_ids[word] for word in list(stop_words)]
        , [-1 for i in range(0,size)]
    )
    
    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], [d for d in data])

def isStopWord(ngram, stop_words=None):
    '''
    ngram :: (Int, String) => (ngram_id, ngram_terms)
    stop_words :: Set of String
    (to avoid SQL query each time isStopWord is invoked, get in as parameter)
    '''
    word = ngram[1]

    if word in stop_words:
        return(True)
    
    def test_match(word, regex):
        format_regex = re.compile(regex)
        if format_regex.match(word) :
            return(True)

    for regex in [
              "^.{1,2}$"
            , "(.*)\d(.*)"
            , "(.*)(\.)(.*)"
            , "(.*)(\,)(.*)"
            , "(.*)(< ?/?p ?>)(.*)"       # marques de paragraphes
            , "(.*)(study)(.*)"
            , "(.*)(xx|xi|xv)(.*)"
            , "(.*)(result)(.*)"
            , "(.*)(année|nombre|moitié)(.*)"
            , "(.*)(temps)(.*)"
            , "(.*)(%)(.*)"
            , "(.*)(\{)(.*)"
            , "(.*)(terme)(.*)"
            , "(.*)(différent)(.*)"
            , "(.*)(travers)(.*)"
            , "(.*)(:|\|)(.*)"
            ] :
        if test_match(word, regex) is True :
            return(True)

def compute_stop(corpus,limit=2000,debug=False):
    '''
    do some statitics on all stop lists of database of the same type
    '''
    stop_node = get_or_create_node(nodetype='StopList', corpus=corpus)
    
    # TODO do a function to get all stop words with social scores
    root = session.query(Node).filter(Node.type_id == cache.NodeType['Root'].id).first()
    root_stop_id = get_or_create_node(nodetype='StopList', corpus=root).id
    
    stop_words = (session.query(Ngram.terms)
                         .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                         .filter(NodeNgram.node_id == root_stop_id)
                         .all()
                 )
    
    #print([n for n in stop_words])
    
    frequency = sa.func.count( NodeNgram.weight )
    ngrams = ( session.query( Ngram.id, Ngram.terms, frequency )
            .join( NodeNgram, NodeNgram.ngram_id == Ngram.id )
            .join( Node, Node.id == NodeNgram.node_id )
            .filter( Node.parent_id == corpus.id, 
                     Node.type_id == cache.NodeType['Document'].id )
            .group_by( Ngram.id )
            .order_by( desc( frequency ) )
            .all()
            #.limit(limit)
            )

    
    ngrams_to_stop = filter(lambda x: isStopWord(x,stop_words=stop_words), ngrams)
    
    #print([n for n in ngrams_to_stop])

    stop = WeightedList({ n[0] : -1 for n in ngrams_to_stop})
    stop.save(stop_node.id)

