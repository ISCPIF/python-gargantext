# Without this, we couldn't use the Django environment
from admin.env import *
#from ngram.stemLem import *

from admin.utils import PrintException

from gargantext_web.db import NodeNgram
from gargantext_web.db import *
from parsing.corpustools import *

import sqlalchemy
from sqlalchemy.sql import func
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from sqlalchemy import literal_column
from sqlalchemy.orm import aliased


from testlists import *
from math import log
from functools import reduce

# use deque
terms =   {'adenoic cystic basal cell carcinoma' : 5
           , 'cystic basal cell carcinoma' : 11
           , 'ulcerated basal cell carcinoma' : 7
           , 'recurrent basal cell carcinoma' : 5
           , 'circumscribed basal cell carcinoma' : 3
           , 'basal cell carcinoma' : 984
           }


def getNgrams(corpus_id=None):
    terms = dict()
    ngrams = (session.query(Ngram.id, Ngram.terms, func.sum(NodeNgram.weight))
                        .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
                        .join(Node, Node.id == NodeNgram.node_id)
                        .filter(Node.parent_id == corpus_id, Node.type_id==cache.NodeType['Document'].id)
                        .group_by(Ngram.id, Ngram.terms)
                        .order_by(desc(func.sum(NodeNgram.weight)))
                        .limit(100)
          )

    for n in ngrams:
        terms[n[1]] = terms[n[2]]
    return(terms)

# frequency :: String -> Int -> Int
def frequency(word, corpus_id=corpus.id):
    terms = getNgrams(corpus_id)
    return(terms.get(word,0))

# includes :: String -> String -> Bool
def includes(string1,string2):
    if string1 == string2:
        return(False)
    else:
        s1 = set(string1.split(' '))
        s2 = set(string2.split(' '))
        return(s1 == s1.intersection(s2))

# included :: String -> [String] -> [String]
# (The result is lazy)
def included(string,listofstring):
    return(filter(lambda x: includes(string,x), listofstring))

# string2freq :: [String] -> [Int]
def string2freq(listofstring, f=frequency):
    return(map(lambda x: f(x), listofstring))

# sumAll :: [Int] -> Int
def sumAll(listofint):
    return(reduce(lambda x,y: x+y, listofint))

# cvalue :: String -> Float
def cvalue(string, listofstring=list(terms.keys())):
    l = [i for i in included(string,listofstring)]
    stringlog = log(len(string.split(' ')),2)
    if len(l) == 0 :
        return(stringlog * frequency(string))
    else:
        frequencyothers = sumAll(string2freq(l))/len(l)
        return(stringlog * (frequency(string) - frequencyothers))

def computeCvalue():
    return('yeah")
# stem all of them first
# connect with the database (frequency)

