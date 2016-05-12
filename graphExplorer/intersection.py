from gargantext.models     import Node, Ngram, NodeNgram, NodeNgramNgram, \
                                  HyperdataKey

from gargantext.util.db    import session, aliased, bulk_insert, func

from gargantext.util.lists import WeightedMatrix, UnweightedList, Translations
from gargantext.util.http  import JsonHttpResponse
from sqlalchemy            import desc, asc, or_, and_, func

import datetime
import ast
import networkx as nx

def intersection(request , corpuses_ids, measure='cooc'):
    '''
    intersection :: (str(Int) + "a" str(Int)) -> Dict(Ngram.id :: Int, Score :: Int)
    intersection = gives the intersection of two graphs

    '''
    if request.method == 'POST' and "nodeids" in request.POST and len(request.POST["nodeids"])>0 :

        node_ids = [int(i) for i in (ast.literal_eval( request.POST["nodeids"] )) ]
        # Here are the visible nodes of the initial semantic map.

        corpuses_ids = corpuses_ids.split('a')

        corpuses_ids = [int(i) for i in corpuses_ids]
        # corpus[1] will be the corpus to compare


            
        def representativity(corpus_id):
            ngrams_data = ( session.query(Ngram.id, NodeNgram)
                                .join(Node, NodeNgram.node_id == Node.id)
                                .filter( Node.parent_id == corpus_id
                                       , Node.typename== 'DOCUMENT')
                                .filter( NodeNgram.weight > 0 )
                                .filter( Ngram.id.in_(node_ids) )
                                .group_by(Ngram.id)
                                .count()
                                )
            nodes_count = ( session.query(Node)
                                   .filter( Node.parent_id == corpus_id
                                          , Node.typename == 'DOCUMENT'
                                          )
                                   .count()
                                   )[0]
        
            result = dict()
            for ngram_id, somme in ngrams_data:
                result[ngram_id] = somme / nodes_count

            return result

        data_0 = representativity(corpuses_ids[0])
        data_1 = representativity(corpuses_ids[1])
        
        queue     = list()

        for k in data_0.keys():
            if data_1[k] == 0:
                queue.append(k)
            else:
                FinalDict[k] = data_0[k] / data_1[k]

        maximum = max([ FinalDict[k] for k in FinalDict.keys()])

        for k in queue:
            FinalDict[k] = maximum +1

        print("-" * 100)
        print(FinalDict)

        return JsonHttpResponse(FinalDict)


