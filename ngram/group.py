# Without this, we couldn't use the Django environment
#from admin.env import *
#from ngram.stemLem import *

from admin.utils import PrintException

from gargantext_web.db import NodeNgram,NodeNodeNgram
from gargantext_web.db import *
from gargantext_web.db import get_or_create_node

from parsing.corpustools import *

from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased


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
                        .join(Ngram, NodeNodeNgram.ngram_id == Ngram.id)
                        .join(Node, Node.id == NodeNodeNgram.nodey_id)
                        .filter(NodeNodeNgram.nodex_id == nodeMeasure_id)
                        .filter(NodeNodeNgram.nodey_id == corpus_id)
                        .group_by(Ngram.id, Ngram.terms, NodeNodeNgram.score)
                        .order_by(desc(NodeNodeNgram.score))
                        .limit(limit)
          )

def getCvalueTfidfNgrams(corpus=None, cvaluelimit=100, tfidflimit=500):
    '''
    getNgrams :: Corpus -> [(Int, String)] -> [(Int, String)]
    For a corpus, gives list of highest Cvalue ngrams and highest TFIDF (global)
    ngrams that have to be grouped with
    '''
    tfidf_node = get_or_create_node(nodetype='Tfidf (global)'
                                    , user_id=corpus.user_id
                                    , parent_id=corpus.id)

    cvalue_node = get_or_create_node(nodetype='Cvalue'
                                    , user_id=corpus.user_id
                                    , parent_id=corpus.id)


    tfidf_ngrams  = queryNodeNodeNgram(nodeMeasure_id=tfidf_node.id, corpus_id=corpus.id, limit=tfidflimit)
    cvalue_ngrams = queryNodeNodeNgram(nodeMeasure_id=cvalue_node.id, corpus_id=corpus.id, limit=cvaluelimit)

    def list2set(_list=None,_set=None):
        for n in _list:
            _set.add((n[0],n[1]))

    tfidf_set = set()
    cvalue_set = set()

    list2set(_list=tfidf_ngrams,_set=tfidf_set)
    list2set(_list=cvalue_ngrams,_set=cvalue_set)

    tfidf_setDiff = tfidf_set.difference(cvalue_set)

    return(cvalue_set,tfidf_setDiff)

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
        return(set(map(lambda x: stemmer.stem(x), ngram[1].split(' '))))

def equals(ngram1,ngram2, f=None):
    '''
    equals :: (Int,String) -> (Int,String) -> Bool
    detect if two ngrams are equivalent according to a function :: String -> [String]
    '''
    if ngram1[0] == ngram2[0]:
    # if ngrams have same id then they are the same (and they can not be
    # grouped)
        return(False)
    else:
        return f(ngram1) == f(ngram2)

def groupNgrams(corpus):
    cvalue,tfidf = getCvalueTfidfNgrams(corpus)
    stemIt = getStemmer(corpus)
    group_to_insert = list()
    node_group_id = get_or_create_node(nodetype='Group', parent_id=corpus.id,user_id=corpus_user_id)
    for n in cvalue:
        group = filter(lambda x: equals(n,x,f=stemIt),tfidf)
        for m in group:
            tfidf.pop(m)
        group_to_insert += (node_group_id, n, m for m in group)


    bulk_insert(NodeNgramNgram, ['node_id', 'ngramx_id', 'ngramy_id', 1], [n for n in group_to_insert])


























