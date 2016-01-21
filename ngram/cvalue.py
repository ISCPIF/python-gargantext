# Without this, we couldn't use the Django environment
#from admin.env import *
#from ngram.stemLem import *

from admin.utils import PrintException,DebugTime

from gargantext_web.db import NodeNgram,NodeNodeNgram
from gargantext_web.db import *
from gargantext_web.db import get_or_create_node, get_session


from parsing.corpustools import *

from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased

#from testlists import *
from math import log
from functools import reduce

from itertools import islice

'''
only for tests if needed (see scientific paper:
Frantzi, K., Ananiadou, S., & Mima, H. (2000). Automatic recognition
of multi-word terms:. the C-value/NC-value method. International
Journal on Digital Libraries, 3(2), 115-130.

ngrams =   {'adenoic cystic basal cell carcinoma' : 5
            , 'cystic basal cell carcinoma' : 11
            , 'ulcerated basal cell carcinoma' : 7
            , 'recurrent basal cell carcinoma' : 5
            , 'circumscribed basal cell carcinoma' : 3
            , 'basal cell carcinoma' : 984
            }
'''

def getNgrams(corpus=None, limit=1000):
    '''
    getNgrams :: Corpus -> [(Int, String, String, Float)]
    '''
    session = get_session()
    
    terms = dict()
    tfidf_node = get_or_create_node(nodetype='Tfidf (global)'
                                    , corpus=corpus)
    #print(corpus.name)
    ngrams = (session.query(Ngram.id, Ngram.terms, func.sum(NodeNgram.weight), NodeNodeNgram.score)
                        .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                        .join(Node, Node.id == NodeNgram.node_id)
                        .join(NodeNodeNgram, NodeNodeNgram.ngram_id == Ngram.id)
                        .filter(NodeNodeNgram.nodey_id == corpus.id, Node.type_id==cache.NodeType['Document'].id)
                        .filter(NodeNodeNgram.nodex_id == tfidf_node.id)
                        .group_by(Ngram.id, Ngram.terms, NodeNodeNgram.score)
                        .order_by(desc(NodeNodeNgram.score))
                        .limit(limit)
          )

    for n in ngrams:
        try:
            nn = list(n)
            terms[nn[1]] = (nn[0],nn[2])
        except:
            PrintException()
    return(terms)
    session.remove()

def compute_cvalue(corpus=None, limit=1000, mysession=None):
    '''
    computeCvalue :: Corpus
    frequency :: String -> Int -> Int
    includes :: String -> String -> Bool

    included :: String -> [String] -> [String]
    (The result is lazy)

    string2freq :: [String] -> [Int]
    sumAll :: [Int] -> Int
    cvalue :: String -> Float
    '''
    dbg = DebugTime('Corpus #%d - cvalue' % corpus.id)
    dbg.show('cvalue')
    terms = getNgrams(corpus=corpus, limit=limit)

    def frequency(word, source=terms):
        return(source.get(word,0)[1])
        #terms = getNgrams(corpus_i)


    def includes(string1,string2):
        if string1 == string2:
            return(False)
        else:
            s1 = set(string1.split(' '))
            s2 = set(string2.split(' '))
            return(s1 == s1.intersection(s2))


    def included(string,listofstring):
        return(filter(lambda x: includes(string,x), listofstring))


    def string2freq(listofstring, f=frequency):
        return(map(lambda x: f(x), listofstring))


    def sumAll(listofint):
        return(reduce(lambda x,y: x+y, listofint))

    def cvalue(string, listofstring=list(terms.keys())):
        l = [i for i in included(string,listofstring)]
        stringlog = log(len(string.split(' ')),2)
        if len(l) == 0 :
            return(stringlog * frequency(string))
        else:
            frequencyothers = sumAll(string2freq(l))/len(l)
            return(stringlog * (frequency(string) - frequencyothers))

    cvalue_node = get_or_create_node(nodetype='Cvalue', corpus=corpus)

    def cvalueAll(listofstring=list(terms.keys())):
        for string in listofstring:
            yield(cvalue_node.id, corpus.id, terms[string][0], cvalue(string))

    result = cvalueAll()
    #print([n for n in result])
    mysession.query(NodeNodeNgram).filter(NodeNodeNgram.nodex_id==cvalue_node.id).delete()
    mysession.commit()

    #bulk_insert(NodeNodeNgram, ['nodex_id', 'nodey_id', 'ngram_id', 'score'], [n for n in islice(result,0,100)])
    bulk_insert(NodeNodeNgram, ['nodex_id', 'nodey_id', 'ngram_id', 'score'], [n for n in result])
# test
#corpus=session.query(Node).filter(Node.id==244250).first()
#computeCvalue(corpus)
