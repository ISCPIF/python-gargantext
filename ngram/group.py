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
        stems = list(map(lambda x: stemmer.stem(x), ngram.split(' ')))
        stems.sort()
        return(str(' '.join(stems)))

    return(stemIt)

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

    frequency = sa.func.count(NodeNgram.weight)
    ngrams = (session.query(Ngram.id, Ngram.terms, frequency )
            .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
            .join(Node, Node.id == NodeNgram.node_id)
            .filter(Node.parent_id==corpus.id, Node.type_id==cache.NodeType['Document'].id)
            .group_by(Ngram.id)
            .order_by(desc(frequency))
            #.all()
            .limit(limit_sup)
            )

    #group = defaultdict(lambda : defaultdict())
    ids_dict = dict()
    mainform_dict = dict()
    count_dict = dict()

    for n in ngrams:
        stem = str(stemIt(n[1]))
        
        if stem is not None :
        
            ids_dict[stem] = ids_dict.get(stem, []) + [n[0]]

            count = count_dict.get(stem, 0)

            if n[2] > count:
                mainform_dict[stem] = n[0]
                count_dict[stem] = n[2]


            for key in mainform_dict.keys():
                miam_to_insert.add((miam_node.id, mainform_dict[key], 1))
                
                try:
                    ids = ids_dict[key]
                    
                    if ids is not None and len(ids) > 1:
                        for ngram_id in ids :
                            if ngram_id != mainform_dict[key]:
                                group_to_insert.add((node_group.id, mainform_dict[key], ngram_id, 1))
                except exception as e:
                    print(e)
                    print(group[stem])

        #print(ids_dict[stem])
    
#    # Deleting previous groups
    session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id == node_group.id).delete()
#    # Deleting previous ngrams miam list
    session.query(NodeNgram).filter(NodeNgram.node_id == miam_node.id).delete()
    session.commit()

    bulk_insert(NodeNgramNgram
                , ('node_id', 'ngramx_id', 'ngramy_id', 'score')
                , [data for data in group_to_insert])

    bulk_insert(NodeNgram, ('node_id', 'ngram_id', 'weight'), [data for data in list(miam_to_insert)])
