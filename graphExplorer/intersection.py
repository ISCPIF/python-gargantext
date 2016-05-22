from gargantext.models     import Node, Ngram, NodeNgram, NodeNgramNgram, \
                                  HyperdataKey

from gargantext.util.db    import session, aliased, bulk_insert, func

from gargantext.util.lists import WeightedMatrix, UnweightedList, Translations
from gargantext.util.http  import JsonHttpResponse
from sqlalchemy            import desc, asc, or_, and_, func

import datetime
import ast
import networkx as nx


def doc_freq(corpus_id, node_ids):
    '''
    doc_freq :: Corpus_id -> [(Ngram_id, Int)]
    Given a corpus, compute number of documents that have the ngram in it.
    '''
    return ( session.query(NodeNgram.ngram_id, func.count(NodeNgram.node_id))
                    .join(Node, NodeNgram.node_id == Node.id)
                    .filter( Node.parent_id == corpus_id
                           , Node.typename== 'DOCUMENT')
                    .filter( NodeNgram.weight > 0 
                           , NodeNgram.ngram_id.in_(node_ids) )
                    .group_by(NodeNgram.ngram_id)
                    .all()
                  )

def doc_ngram_representativity(corpus_id, node_ids):
    '''
    doc_ngram_representativity :: Corpus_ID -> Dict Ngram_id Float
    Given a corpus, compute part of of documents that have the ngram it it.
    '''
    nodes_count = ( session.query(Node)
                           .filter( Node.parent_id == corpus_id
                                  , Node.typename == 'DOCUMENT'
                                  )
                           .count()
                  )

    result = dict()
    for ngram_id, somme in doc_freq(corpus_id, node_ids):
        result[ngram_id] = somme / nodes_count

    return result

def compare_corpora(Corpus_id_A, Corpus_id_B, node_ids):
    '''
    compare_corpora :: Corpus_id -> Corpus_id -> Dict Ngram_id Float
    Given two corpus :
        - if corpora are the same, it return :
            (dict of document frequency per ngram as key)
        - if corpora are different, it returns :
            doc_ngram_representativit(Corpus_id_A) / doc_ngram_representativity(Corpus_id_B)
            (as dict per ngram as key)
    '''

    result = dict()
    
    if int(Corpus_id_A) == int(Corpus_id_B):
        for ngram_id, somme in doc_freq(Corpus_id_A, node_ids):
            result[ngram_id] = somme
    
    else:

        data_A = doc_ngram_representativity(Corpus_id_A, node_ids)
        data_B = doc_ngram_representativity(Corpus_id_B, node_ids)
    
        queue     = list()

        for k in data_A.keys():
            if k not in data_B.keys():
                queue.append(k)
            else:
                result[k] = data_B[k] / data_A[k]

        maximum = max([ result[k] for k in result.keys()])
        minimum = min([ result[k] for k in result.keys()])

        for k in queue:
            result[k] = minimum

    return result

def intersection(request , corpuses_ids, measure='cooc'):
    '''
    intersection :: (str(Int) + "a" str(Int)) -> Dict(Ngram.id :: Int, Score :: Int)
    intersection = returns as Json Http Response the intersection of two graphs

    '''
    if request.method == 'POST' and "nodeids" in request.POST and len(request.POST["nodeids"])>0 :

        node_ids = [int(i) for i in (ast.literal_eval( request.POST["nodeids"] )) ]
        # Here are the visible nodes of the initial semantic map.

        corpuses_ids = corpuses_ids.split('a')

        corpuses_ids = [int(i) for i in corpuses_ids]
        # corpus[1] will be the corpus to compare
        
        return JsonHttpResponse(compare_corpora(corpuses_ids[0], corpuses_ids[1], node_ids))

