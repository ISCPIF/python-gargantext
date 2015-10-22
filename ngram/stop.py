# Without this, we couldn't use the Django environment
#from admin.env import *
#from ngram.stemLem import *

import re
from admin.utils import PrintException

from gargantext_web.db import NodeNgram,NodeNodeNgram
from gargantext_web.db import cache, session, get_or_create_node

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

    for regex in ["(.*)\d(.*)"
            , "^.{1,2}$"
            , "(.*)(\.)(.*)"
            , "(.*)(\,)(.*)"
            , "(.*)(study)(.*)"
            , "(.*)(result)(.*)"
            , "(.*)(année)(.*)"
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


def compute_stop(corpus,size=2000,debug=False):
    '''
    do some statitics on all stop lists of database of the same type
    '''
    stop_node = get_or_create_node(nodetype='StopList', corpus=corpus)
    miam_node = get_or_create_node(nodetype='MiamList', corpus=corpus)
    
    # TODO do a function to get all stop words with social scores
    root = session.query(Node).filter(Node.type_id == cache.NodeType['Root'].id).first()
    root_stop_id = get_or_create_node(nodetype='StopList', corpus=root).id
    
    stop_words = (session.query(Ngram.terms)
                         .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                         .filter(NodeNgram.node_id == root_stop_id)
                         .all()
                 )

    top_words = (session.query(Ngram.id, Ngram.terms)
                .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                .filter(NodeNgram.node_id == miam_node.id)
                .order_by(desc(NodeNgram.weight))
                .limit(size)
                )
    
    ngrams_to_stop = filter(lambda x: isStopWord(x,stop_words=stop_words), top_words)
    
    stop = WeightedList({ n[0] : -1 for n in ngrams_to_stop})
    stop.save(stop_node.id)

    miam = UnweightedList(miam_node.id)

    new_miam = miam - stop
    new_miam.save(miam_node.id)

#    data = zip(
#        [stop_node.id for i in range(0,size)]
#        , [ngram[0] for ngram in ngrams_to_stop]
#        , [-1 for i in range(0,size)]
#    )
#    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], [d for d in data])


#corpus=session.query(Node).filter(Node.id==545461).first()
#compute_stop(corpus)



