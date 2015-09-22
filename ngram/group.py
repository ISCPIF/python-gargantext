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


def queryNodeNodeNgram(nodeMeasure_id=None, corpus_id=None, size=None):
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
    if size is None:
        query = query.count()
    else:
        query = query.limit(size)
    return(query)

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

    tfidf_ngrams  = queryNodeNodeNgram(nodeMeasure_id=tfidf_node.id, corpus_id=corpus.id, size=tfidflimit)
    cvalue_ngrams = queryNodeNodeNgram(nodeMeasure_id=cvalue_node.id, corpus_id=corpus.id, size=cvaluelimit)

    #print([n for n in tfidf_ngrams])

    def list2set(_list,_set):
        for n in _list:
            _set.add((n[0],n[1]))

    tfidf_set = set()
    cvalue_set = set()

    list2set(tfidf_ngrams,tfidf_set)
    list2set(cvalue_ngrams,cvalue_set)

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

    return(stemIt)

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
        try:
            return f(ngram1) == f(ngram2)
        except:
            return(False)
            PrintException()

def groupNgrams(corpus):
# rename it
    cvalue,tfidf = getCvalueTfidfNgrams(corpus)
    stemIt = getStemmer(corpus)

    group_to_insert = list()
    node_group = get_or_create_node(nodetype='Group',parent_id=corpus.id,user_id=corpus.user_id)

    miam_to_insert = set()
    miam_node = get_or_create_node(nodetype='MiamList',parent_id=corpus.id,user_id=corpus.user_id)

    list_to_check=tfidf.union(cvalue)
    #print(cvalue)
    #print(equals((0,'bee'),(1,'bees'),f=stemIt))
    for n in cvalue:
        group = filter(lambda x: equals(n,x,f=stemIt),list_to_check)
        miam_to_insert.add((miam_node.id, n[0],1))
        #print([n for n in group])
        for g in group:
            #list_to_check.remove(g)
            group_to_insert.append((node_group.id, n[0], g[0], 1))
            print(n[1], "=", g[1])
    # Deleting previous groups
    session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==node_group.id).delete()
    bulk_insert(NodeNgramNgram, ('node_id', 'ngramx_id', 'ngramy_id', 'score'), [data for data in group_to_insert])
#
#    # stop_id = get_or_create_node(parent_id=corpus.id,user_id=corpus.user_id,nodetype='StopList')
    session.query(NodeNgram).filter(NodeNgram.node_id==miam_node.id).delete()
    #session.commit()
    for n in group_to_insert:
        print(n)
        miam_to_insert.add((miam_node.id, n[1], 1))
    # Deleting previous ngrams miam list
    bulk_insert(NodeNgram, ('node_id', 'ngram_id', 'weight'), [data for data in list(miam_to_insert)])


    # cvalue - stop list => miam list here


corpus = session.query(Node).filter(Node.id==244074).first()
groupNgrams(corpus)

