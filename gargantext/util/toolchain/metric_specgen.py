"""
Computes a specificity metric from the ngram cooccurrence matrix.
 + SAVE => WeightedList => NodeNgram
"""
from gargantext.models        import Node, Ngram, NodeNgram, NodeNgramNgram
from gargantext.util.db       import session, aliased, func, bulk_insert
from gargantext.util.lists    import WeightedList
from collections              import defaultdict
from pandas                   import DataFrame
from numpy                    import diag

def round3(floating_number):
    """
    Rounds a floating number to 3 decimals
    Good when we don't need so much details in the DB writen data
    """
    return float("%.3f" % floating_number)

def compute_specgen(corpus, cooc_id=None, cooc_matrix=None,
                    spec_overwrite_id = None, gen_overwrite_id = None):
    '''
    Compute genericity/specificity:
        P(j|i) = N(ij) / N(ii)
        P(i|j) = N(ij) / N(jj)

        Gen(i)  = Mean{j} P(j_k|i)
        Spec(i) = Mean{j} P(i|j_k)

        Gen-clusion(i)  = (Spec(i) + Gen(i)) / 2
        Spec-clusion(i) = (Spec(i) - Gen(i)) / 2

    Parameters:
        - cooc_id: mandatory id of a cooccurrences node to use as base
        - spec_overwrite_id: optional preexisting specificity node to overwrite
        - gen_overwrite_id: optional preexisting genericity node to overwrite
    '''

    matrix = defaultdict(lambda : defaultdict(float))

    if cooc_id == None and cooc_matrix == None:
        raise TypeError("compute_specificity: needs a cooc_id or cooc_matrix param")

    elif cooc_id:
        cooccurrences = (session.query(NodeNgramNgram)
                        .filter(NodeNgramNgram.node_id==cooc_id)
                        )
        # no filtering: cooc already filtered on mainlist_id at creation
        for cooccurrence in cooccurrences:
            matrix[cooccurrence.ngram1_id][cooccurrence.ngram2_id] = cooccurrence.weight
            # matrix[cooccurrence.ngram2_id][cooccurrence.ngram1_id] = cooccurrence.weight

    elif cooc_matrix:
        # copy WeightedMatrix into local matrix structure
        for (ngram1_id, ngram2_id) in cooc_matrix.items:

            w = cooc_matrix.items[(ngram1_id, ngram2_id)]
            # ------- 8< --------------------------------------------
            # tempo hack to ignore lines/columns where diagonal == 0
            # £TODO find why they exist and then remove this snippet
            if (((ngram1_id,ngram1_id) not in cooc_matrix.items) or
                ((ngram2_id,ngram2_id) not in cooc_matrix.items)):
                continue
            # ------- 8< --------------------------------------------
            matrix[ngram1_id][ngram2_id] = w

    nb_ngrams = len(matrix)

    print("SPECIFICITY: computing on %i ngrams" % nb_ngrams)

    # example corpus (7 docs, 8 nouns)
    # --------------------------------
    # "The report says that humans are animals."
    # "The report says that rivers are full of water."
    # "The report says that humans like to make war."
    # "The report says that animals must eat food."
    # "The report says that animals drink water."
    # "The report says that humans like food and water."
    # "The report says that grass is food for some animals."

    #===========================================================================
    cooc_counts = DataFrame(matrix).fillna(0)

    # cooc_counts matrix
    # ------------------
    #           animals  food  grass  humans  report  rivers  war  water
    # animals         4     2      1       1       4       0    0      1
    # food            2     3      1       1       3       0    0      1
    # grass           1     1      1       0       1       0    0      0
    # humans          1     1      0       3       3       0    1      1
    # report          4     3      1       3       7       1    1      3
    # rivers          0     0      0       0       1       1    0      1
    # war             0     0      0       1       1       0    1      0
    # water           1     1      0       1       3       1    0      3

    #===========================================================================
    # conditional p(col|line)
    diagonal = list(diag(cooc_counts))


    # debug
    # print("WARN diag: ", diagonal)
    # print("WARN diag: =================== 0 in diagonal ?\n",
    #         0 in diagonal ? "what ??? zeros in the diagonal :/" : "ok no zeros",
    #         "\n===================")

    p_col_given_line = cooc_counts / list(diag(cooc_counts))

    # p_col_given_line
    # ----------------
    #          animals  food  grass  humans  report rivers   war  water
    # animals      1.0   0.7    1.0     0.3     0.6    0.0   0.0    0.3
    # food         0.5   1.0    1.0     0.3     0.4    0.0   0.0    0.3
    # grass        0.2   0.3    1.0     0.0     0.1    0.0   0.0    0.0
    # humans       0.2   0.3    0.0     1.0     0.4    0.0   1.0    0.3
    # report       1.0   1.0    1.0     1.0     1.0    1.0   1.0    1.0
    # rivers       0.0   0.0    0.0     0.0     0.1    1.0   0.0    0.3
    # war          0.0   0.0    0.0     0.3     0.1    0.0   1.0    0.0
    # water        0.2   0.3    0.0     0.3     0.4    1.0   0.0    1.0

    #===========================================================================
    # total per lines (<=> genericity)
    Gen = p_col_given_line.sum(axis=1)

    # Gen.sort_values(ascending=False)
    # ---
    # report    8.0
    # animals   3.9
    # food      3.6
    # water     3.3
    # humans    3.3
    # grass     1.7
    # war       1.5
    # rivers    1.5

    #===========================================================================
    # total columnwise (<=> specificity)
    Spec = p_col_given_line.sum(axis=0)

    # Spec.sort_values(ascending=False)
    # ----
    # grass     4.0
    # food      3.7
    # water     3.3
    # humans    3.3
    # report    3.3
    # animals   3.2
    # war       3.0
    # rivers    3.0


    #===========================================================================
    # our "inclusion by specificity" metric
    Specclusion = Spec-Gen

    # Specclusion.sort_values(ascending=False)
    # -----------
    # grass      1.1
    # war        0.8
    # rivers     0.8
    # food       0.0
    # humans    -0.0
    # water     -0.0
    # animals   -0.3
    # report    -2.4

    #===========================================================================
    # our "inclusion by genericity" metric
    Genclusion = Spec+Gen

    # Genclusion.sort_values(ascending=False)
    # -----------
    # report     11.3
    # food        7.3
    # animals     7.2
    # water       6.7
    # humans      6.7
    # grass       5.7
    # war         4.5
    # rivers      4.5

    #===========================================================================
    # specificity node
    if spec_overwrite_id:
        # overwrite pre-existing id
        the_spec_id = spec_overwrite_id
        session.query(NodeNgram).filter(NodeNgram.node_id==the_spec_id).delete()
        session.commit()
    else:
        specnode = corpus.add_child(
            typename  = "SPECCLUSION",
            name = "Specclusion (in:%s)" % corpus.id
        )
        session.add(specnode)
        session.commit()
        the_spec_id = specnode.id

    if not Specclusion.empty:
        data = WeightedList(
                zip(  Specclusion.index.tolist()
                    , [v for v  in map(round3, Specclusion.values.tolist())]
                 )
               )
        data.save(the_spec_id)
    else:
        print("WARNING: had no terms in COOCS => empty SPECCLUSION node")

    #===========================================================================
    # genclusion node
    if gen_overwrite_id:
        the_gen_id = gen_overwrite_id
        session.query(NodeNgram).filter(NodeNgram.node_id==the_gen_id).delete()
        session.commit()
    else:
        gennode = corpus.add_child(
            typename  = "GENCLUSION",
            name = "Genclusion (in:%s)" % corpus.id
        )
        session.add(gennode)
        session.commit()
        the_gen_id = gennode.id

    if not Genclusion.empty:
        data = WeightedList(
                zip(  Genclusion.index.tolist()
                    , [v for v  in map(round3, Genclusion.values.tolist())]
                 )
               )
        data.save(the_gen_id)
    else:
        print("WARNING: had no terms in COOCS => empty GENCLUSION node")

    #===========================================================================
    return(the_spec_id, the_gen_id)
