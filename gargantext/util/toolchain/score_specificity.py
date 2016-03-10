from gargantext.util.db import session, aliased, func
from gargantext.util.db_cache import *
from gargantext.constants import *

# from gargantext.util.analysis.cooccurrences import do_cooc

from gargantext.models import Node, Ngram, NodeNgramNgram, NodeNodeNgram

import pandas as pd
from collections import defaultdict

def compute_specificity(corpus, cooc_id, limit=100):
    '''
    Compute the specificity, simple calculus.
    '''

    cooccurrences = (session.query(NodeNgramNgram)
                    .filter(NodeNgramNgram.node_id==cooc_id)
                    # no filtering: new choice filter on tfidf before creation
                    #    .order_by(NodeNgramNgram.weight)
                    #    .limit(limit)
                    )

    matrix = defaultdict(lambda : defaultdict(float))

    # £TODO re-rename weight => score
    for cooccurrence in cooccurrences:
        matrix[cooccurrence.ngram1_id][cooccurrence.ngram2_id] = cooccurrence.weight
        matrix[cooccurrence.ngram2_id][cooccurrence.ngram1_id] = cooccurrence.weight

    nb_ngrams = len(matrix)

    d = pd.DataFrame(matrix).fillna(0)

    # proba (x/y) ( <= on divise chaque colonne par son total)
    d = d / d.sum(axis=0)

    # d:Matrix => v: Vector (len = nb_ngrams)
    v = d.sum(axis=1)

    ## d ##
    #######
    #               Grenelle  biodiversité  kilomètres  site  élus  île
    # Grenelle             0             0           4     0     0    0
    # biodiversité         0             0           0     0     4    0
    # kilomètres           4             0           0     0     4    0
    # site                 0             0           0     0     4    6
    # élus                 0             4           4     4     0    0
    # île                  0             0           0     6     0    0


    ## d.sum(axis=1) ##
    ###################
    # Grenelle         4
    # biodiversité     4
    # kilomètres       8
    # site            10
    # élus            12
    # île              6

    # résultat temporaire
    # -------------------
    # pour l'instant on va utiliser les sommes en ligne comme ranking de spécificité
    # (**même** ordre qu'avec la formule d'avant le refactoring mais calcul + simple)
    # TODO analyser la cohérence math ET sem de cet indicateur
    v.sort_values(inplace=True)

    # [ ('biodiversité' , 0.333 ),
    #   ('Grenelle'     , 0.5   ),
    #   ('île'          , 0.599 ),
    #   ('kilomètres'   , 1.333 ),
    #   ('site'         , 1.333 ),
    #   ('élus'         , 1.899 ) ]

    # ----------------
    # specificity node
    node = session.query(Node).filter(
        Node.parent_id==corpus.id,
        Node.typename == "SPECIFICITY"
        ).first()

    if node == None:
        user_id = corpus.user_id
        node = Node(name="Specif (in:%i)" % corpus.id,
                    parent_id=corpus.id,
                    user_id=user_id,
                    typename="SPECIFICITY")
        session.add(node)
        session.commit()

    data = zip(  [node.id] * nb_ngrams
               , [corpus.id] * nb_ngrams
               , v.index.tolist()
               , v.values.tolist()
               )
    session.query(NodeNodeNgram).filter(NodeNodeNgram.node1_id==node.id).delete()
    session.commit()

    bulk_insert(NodeNodeNgram, ['node1_id', 'node2_id', 'ngram_id', 'score'], [d for d in data])

    return(node.id)
