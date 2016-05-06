from gargantext.models     import Node, Ngram, NodeNgram, NodeNgramNgram, \
                                  HyperdataKey

from gargantext.util.db    import session, aliased, bulk_insert, func

from gargantext.util.lists import WeightedMatrix, UnweightedList, Translations
from gargantext.util.http  import JsonHttpResponse
from sqlalchemy            import desc, asc, or_, and_

import datetime

def intersection(request , corpuses_ids, measure='cooc'):
    FinalDict = False
    if request.method == 'POST' and "nodeids" in request.POST and len(request.POST["nodeids"])>0 :

        import ast
        import networkx as nx
        node_ids = [int(i) for i in (ast.literal_eval( request.POST["nodeids"] )) ]
        # Here are the visible nodes of the initial semantic map.

        corpuses_ids = corpuses_ids.split('a')

        corpuses_ids = [int(i) for i in corpuses_ids]
        print(corpuses_ids)
        # corpus[1] will be the corpus to compare



        def get_score(corpus_id):

            cooc_ids  = (session.query(Node.id)
                                .filter(Node.user_id == request.user.id
                                      , Node.parent_id==corpus_id
                                      , Node.typename == 'COOCCURRENCES' )
                                .first()
                                )

            if len(cooc_ids)==0:
                return JsonHttpResponse(FinalDict)
                # If corpus[1] has a coocurrence.id then lets continue

            Coocs  = {}

            G = nx.Graph()
            # undirected graph only
            # because direction doesnt matter here
            # coocs is triangular matrix

            ngrams_data = ( session.query(NodeNgramNgram)
                                   .filter( NodeNgramNgram.node_id==cooc_ids[0]
                                          , or_( NodeNgramNgram.ngram1_id.in_( node_ids )
                                               , NodeNgramNgram.ngram2_id.in_( node_ids )
                                               )
                                          )
                                   .group_by(NodeNgramNgram)
                                   .all()
                                   )

            for ngram in ngrams_data :
                # are there visible nodes in the X-axis of corpus to compare ?
                G.add_edge(  ngram.ngram1_id ,  ngram.ngram2_id , weight=ngram.weight)
                print(corpus_id, ngram)

            for e in G.edges_iter() :
                n1 = e[0]
                n2 = e[1]
                # print( G[n1][n2]["weight"] , "\t", n1,",",n2 )

                if n1 not in Coocs :
                    Coocs[n1] = 0

                if n2 not in Coocs :
                    Coocs[n2] = 0

                Coocs[n1] += G[n1][n2]["weight"]
                Coocs[n2] += G[n1][n2]["weight"]

            return(Coocs,G)

        Coocs_0,G_0 = get_score( corpuses_ids[0] )
        Coocs_1,G_1 = get_score( corpuses_ids[1] )

        FinalDict = {}

        if measure == 'jacquard':
            for node in node_ids :
                if node in G_1.nodes() and node in G_0.nodes():
                    neighbors_0 = set(G_0.neighbors(node))
                    neighbors_1 = set(G_1.neighbors(node))
                    jacquard = len(neighbors_0.intersection(neighbors_1)) / len(neighbors_0.union(neighbors_1))
                    FinalDict[node] = jacquard * 3
                elif node in G_0.nodes() and node not in G_1.nodes() :
                    FinalDict[node] = 2
                elif node not in G_0.nodes() and node in G_1.nodes() :
                    FinalDict[node] = 1
                else:
                    FinalDict[node] = 0

        elif measure == 'degree':
            for node in node_ids :
                if node in G_1.nodes() and node in G_0.nodes():
                    score_0 = Coocs_0[node] / G_0.degree(node)
                    score_1 = Coocs_1[node] / G_1.degree(node)
                    FinalDict[node] = 5 * score_0 / score_1
                elif node in G_0.nodes() and node not in G_1.nodes() :
                    FinalDict[node] = 0.5
                elif node not in G_0.nodes() and node in G_1.nodes() :
                    FinalDict[node] = 0.2
                else:
                    FinalDict[node] = 0

        elif measure == 'cooc':
            for node in node_ids :
                if node in G_1.nodes() and node in G_0.nodes():
                    #FinalDict[node] = Coocs_1[node] / Coocs_0[node]
                    FinalDict[node] = Coocs_0[node] / Coocs_1[node]
                elif node in G_0.nodes() and node not in G_1.nodes() :
                    FinalDict[node] = 0.0
                elif node not in G_0.nodes() and node in G_1.nodes() :
                    FinalDict[node] = 0.0
                else:
                    FinalDict[node] = 0



        print(FinalDict)
                #print(node,score)
                # Getting AVG-COOC of each ngram that exists in the cooc-matrix of the compared-corpus.

    return JsonHttpResponse(FinalDict)


