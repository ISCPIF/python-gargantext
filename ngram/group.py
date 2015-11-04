# Without this, we couldn't use the Django environment
#from admin.env import *

from admin.utils import PrintException,DebugTime

from gargantext_web.db import NodeNgram,NodeNodeNgram
from gargantext_web.db import *
from gargantext_web.db import get_or_create_node

from parsing.corpustools import *

import sqlalchemy as sa
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

from collections import defaultdict

#from testlists import *
from math import log
from functools import reduce

def queryNodeNodeNgram(nodeMeasure_id=None, corpus_id=None, limit=None):
    '''
    queryNodeNodeNgram :: Int -> Int -> Int -> (Int, String, Float)
    Get list of ngrams according to a measure related to the corpus: maybe tfidf
    cvalue.
    '''
    query = (session.query(Ngram.id, Ngram.terms, NodeNodeNgram.score)
                    .join(NodeNodeNgram, NodeNodeNgram.ngram_id == Ngram.id)
                    .join(Node, Node.id == NodeNodeNgram.nodex_id)
                    .filter(NodeNodeNgram.nodex_id == nodeMeasure_id)
                    .filter(NodeNodeNgram.nodey_id == corpus_id)
                    .group_by(Ngram.id, Ngram.terms, NodeNodeNgram.score)
                    .order_by(desc(NodeNodeNgram.score))
            )

    if limit is None:
        query = query.count()
    elif limit == 0 :
        query = query.all()
    else:
        query = query.limit(limit)

    return(query)

def getNgrams(corpus=None, limit_inf=600, limit_sup=3000):
    '''
    getNgrams :: Corpus -> [(Int, String)] -> [(Int, String)]
    For a corpus, gives list of highest Cvalue ngrams and highest TFIDF (global)
    ngrams that have to be grouped with
    '''
    #tfidf_node = get_or_create_node(nodetype='Tfidf (global)', corpus=corpus)
    cvalue_node = get_or_create_node(nodetype='Cvalue', corpus=corpus)
    spec_node = get_or_create_node(nodetype='Specificity', corpus=corpus)


    #tfidf_ngrams  = queryNodeNodeNgram(nodeMeasure_id=tfidf_node.id, corpus_id=corpus.id)
    cvalue_ngrams = queryNodeNodeNgram(nodeMeasure_id=cvalue_node.id, corpus_id=corpus.id, limit=limit_sup)
    spec_ngrams   = queryNodeNodeNgram(nodeMeasure_id=spec_node.id, corpus_id=corpus.id, limit=limit_inf)

    #print([n for n in tfidf_ngrams])

    def list2set(_list):
        _set = set()
        for n in _list:
            _set.add((n[0],n[1]))
        return(_set)

    cvalue_set = set()
    spec_set = set()

    cvalue_set = list2set(cvalue_ngrams)
    spec_set   = list2set(spec_ngrams)

    cvalue_setDiff = cvalue_set.difference(spec_set)

    return(spec_set,cvalue_setDiff)

def getStemmer(corpus):
    '''
    getStemmer :: Corpus -> Stemmer
    Get the stemmer
    TODO: need to be generic for all languages
    '''
    if corpus.language_id is None or corpus.language_id == cache.Language['en'].id:
        from nltk.stem.porter import PorterStemmer
        stemmer = PorterStemmer()
        #stemmer.stem('honeybees')
    elif corpus.language_id == cache.Language['fr'].id:
        from nltk.stem.snowball import FrenchStemmer
        stemmer = FrenchStemmer()
        #stemmer.stem('abeilles')
    else:
        print("No language found")

    def stemIt(ngram):
        return(list(map(lambda x: stemmer.stem(x), ngram.split(' '))).sort())

    return(stemIt)

def equals(ngram1,ngram2, f=None):
    '''
    equals :: (Int,String) -> (Int,String) -> Bool
    detect if two ngrams are equivalent according to a function :: String -> [String]
    '''
    if ngram1[0] == ngram2[0]:
    # if ngrams have same id then they are the same 
    # and they can not be grouped
        return(False)
    else:
        try:
            return f(ngram1) == f(ngram2)
        except:
            return(False)
            PrintException()

def compute_groups(corpus, limit_inf=None, limit_sup=None, how='Stem'):
    '''
    group ngrams according to a function (stemming or lemming)
    '''
    dbg = DebugTime('Corpus #%d - group' % corpus.id)
    dbg.show('Group')

    #spec,cvalue = getNgrams(corpus, limit_inf=limit_inf, limit_sup=limit_sup)
    #list_to_check=cvalue.union(spec)

    if how == 'Stem':
        stemIt = getStemmer(corpus)

    group_to_insert = set()
    node_group = get_or_create_node(nodetype='Group', corpus=corpus)

    miam_to_insert = set()
    miam_node = get_or_create_node(nodetype='MiamList', corpus=corpus)

    somme = sa.func.count(NodeNgram.weight)
    ngrams = (session.query(Ngram.id, Ngram.terms, somme )
            .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
            .join(Node, Node.id == NodeNgram.node_id)
            .filter(Node.parent_id==corpus.id, Node.type_id==cache.NodeType['Document'].id)
            .group_by(Ngram.id)
            .order_by(desc(somme))
            .all()
            #.limit(limit_sup)
            )

    group = defaultdict(lambda : defaultdict())

    for n in ngrams:
        stem = stemIt(n[1])
        maincount = group[stem].get('count', 0)

        if n[2] > maincount:
            group[stem]['main form'] = n[0]
            group[stem]['count'] = n[2]
        else:
            group[stem]['ids'] = group[stem].get('ids', []) + [n[0]]

    for stem in group.keys():
        miam_to_insert.add((miam_node.id, group[stem]['main form'], 1))
        for ngram_id in group[stem]['ids']:
            group_to_insert.add((node_group.id, group[stem]['main form'], ngram_id, 1))

    # TODO see here if coherent add in miam or group...
    # Deleting previous groups
    session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id == node_group.id).delete()
    bulk_insert(NodeNgramNgram
                , ('node_id', 'ngramx_id', 'ngramy_id', 'score')
                , [data for data in group_to_insert])

    for n in group_to_insert:
        #print(n)
        miam_to_insert.add((miam_node.id, n[1], 1))
    
    # Deleting previous ngrams miam list
    session.query(NodeNgram).filter(NodeNgram.node_id == miam_node.id).delete()
    bulk_insert(NodeNgram, ('node_id', 'ngram_id', 'weight'), [data for data in list(miam_to_insert)])
