"""
Computes a specificity metric from the ngram cooccurrence matrix.
 + SAVE => WeightedList => NodeNgram
"""
from gargantext.models        import Node, Ngram, NodeNgram, NodeNgramNgram
from gargantext.util.db       import session, aliased, func, bulk_insert
from gargantext.util.lists    import WeightedList
from collections              import defaultdict
from pandas                   import DataFrame

def compute_specificity(corpus, cooc_id=None, overwrite_id = None):
    '''
    Compute the specificity, simple calculus.

    Parameters:
        - cooc_id: mandatory id of a cooccurrences node to use as base
        - overwrite_id: optional preexisting specificity node to overwrite
    '''

    cooccurrences = (session.query(NodeNgramNgram)
                    .filter(NodeNgramNgram.node_id==cooc_id)
                    )
    # no filtering: new choice cooc already filtered on tfidf before creation

    matrix = defaultdict(lambda : defaultdict(float))

    # £TODO re-rename weight => score
    for cooccurrence in cooccurrences:
        matrix[cooccurrence.ngram1_id][cooccurrence.ngram2_id] = cooccurrence.weight
        matrix[cooccurrence.ngram2_id][cooccurrence.ngram1_id] = cooccurrence.weight

    nb_ngrams = len(matrix)

    print("SPECIFICITY: computing on %i ngrams" % nb_ngrams)

    d = DataFrame(matrix).fillna(0)

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
    if overwrite_id:
        # overwrite pre-existing id
        the_id = overwrite_id
        session.query(NodeNodeNgram).filter(NodeNodeNgram.node1_id==the_id).delete()
        session.commit()
    else:
        specnode = corpus.add_child(
            typename  = "SPECIFICITY",
            name = "Specif (in:%s)" % corpus.id
        )
        session.add(specnode)
        session.commit()
        the_id = specnode.id

    # print(v)

    data = WeightedList(
            zip(  v.index.tolist()
                , v.values.tolist()
             )
           )
    data.save(the_id)

    return(the_id)
