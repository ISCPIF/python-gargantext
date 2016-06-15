"""
Utilities for group management
  - query_grouped_ngrams(group_id) to retrieve subforms
  - group_union() to join two groupings lists
"""
from gargantext.util.db  import session, aliased
from gargantext.models   import Ngram, NodeNgramNgram
from igraph              import Graph  # for group_union

def query_groups(groupings_id, details=False):
    """
    Listing of couples (mainform,   subform)
                 aka   (ngram1_id, ngram2_id)

    Parameter:
      - details: if False, just send the array of couples
                 if True, send quadruplets with (ngram1_id, term1, ngram2_id, term2)
    """
    if not details:
        # simple contents
        query = session.query(NodeNgramNgram.ngram1_id, NodeNgramNgram.ngram2_id)
    else:
        # detailed contents (id + terms)
        Ngram1 = aliased(Ngram)
        Ngram2 = aliased(Ngram)
        query = (session
                    .query(
                        NodeNgramNgram.ngram1_id,
                        Ngram1.terms,
                        NodeNgramNgram.ngram2_id,
                        Ngram2.terms,
                     )
                    .join(Ngram1, NodeNgramNgram.ngram1_id == Ngram1.id)
                    .join(Ngram2, NodeNgramNgram.ngram2_id == Ngram2.id)
                )

    # main filter
    # -----------
    query = query.filter(NodeNgramNgram.node_id == groupings_id)

    return query

def query_grouped_ngrams(groupings_id, details=False, scoring_metric_id=None):
    """
    Listing of "hidden" ngram_ids from the groups

    Works only for grouplists

    Parameter:
      - details: if False, send just the array of ngram_ids
                 if True, send triples with (ngram_id, term, scoring)
                                                             ^^^^^^^

      deprecated: scoring_metric_id: id of a scoring metric node   (TFIDF or OCCS)
                           (for details and sorting)
                   (no more OCCS counts of subforms)
    """
    if not details:
        # simple contents
        query = session.query(NodeNgramNgram.ngram2_id)
    else:
        # detailed contents (terms and some NodeNodeNgram for score)
        query = (session
                    .query(
                        NodeNgramNgram.ngram2_id,
                        Ngram.terms,
                        # NodeNodeNgram.score           #
                     )
                    .join(Ngram, NodeNgramNgram.ngram2_id == Ngram.id)
                    # .join(NodeNodeNgram, NodeNgramNgram.ngram2_id == NodeNodeNgram.ngram_id)
                    # .filter(NodeNodeNgram.node1_id == scoring_metric_id)
                    # .order_by(desc(NodeNodeNgram.score))
                )

    # main filter
    # -----------
    query = query.filter(NodeNgramNgram.node_id == groupings_id)

    return query


def group_union(g_a_links, g_b_links):
    """
    Synonym groups are modelled by sets of couples in the DB

    Input : 2 arrays of links (ngramx_id, ngramy_id)
    Input : 1 array of links (ngramx_id, ngramy_id)

    Synonymity is considered transitive so in effect the groups
    can form a set (defined by the connected component of couples).

     A requested feature is also that one node dominates others
     (aka "leader effect"; leader will be in the map, the others won't)

    Summary of major union effects in various cases:

    GROUP 1         Group 2         Group 1 ∪ 2

    A -> B           A -> C           A -> B       (simple union)
                                      A -> C

    D -> E           E -> F           D -> E
                                      D -> F       (D "leader effect")


    G -> H           G -> I           G -> H       ( transitivity +
                     H -> J           G -> I        "leader effect")
                                      G -> J

     rloth: this is some slightly amended code
     from Samuel's in rest_v1_0.ngrams.Group.get

     TODO use "most frequent" score if leader candidates are ex aequo by degree.
    """

    # output: list of links forming new group
    new_links = []

    # 1) create graph with both lists
    # -------------------------------

    # from igraph import Graph

    # the set of all our ngram_ids
    all_vertices = set(
      [ngid for couple in g_a_links+g_b_links for ngid in couple]
    )

    # initialize the synonym graph with size
    sg = Graph(len(all_vertices), directed=True)

    # add our IDs as "name" (special attribute good for edge creation)
    sg.vs['name'] = [str(x) for x in all_vertices]

    # add the edges as named couples
    sg.add_edges([(str(x),str(y)) for (x,y) in g_a_links])

    #print('UNION A:', g_a_links)
    #print('initially %i components' % len(sg.as_undirected().components()))

    # same with the other edges
    sg.add_edges([(str(x),str(y)) for (x,y) in g_b_links])

    #print('UNION B:', g_b_links)
    #print('after union %i components' % len(sg.as_undirected().components()))


    # 2) list resulting components
    # -----------------------------
    synonym_components = sg.as_undirected().components()

    # for example
    # cs = [[0, 3, 6], [1, 2, 8], [4, 5, 9, 11], [7,10]]

    # there should be no singletons by construction

    # list of all outdegrees for "leader" detection
    # (leader = term most often marked as source by the users)
    odegs = sg.outdegree()

    #for i, v in enumerate(sg.vs):
    #    print("%i - name:%s - odeg:%i" % (i, v['name'], odegs[i]))

    for component in synonym_components:
        # we map back to our ids, preserving order
        our_comp = [int(our_id) for our_id in sg.vs[component]['name']]

        # 3) take main node and unnest into new links list
        # -------------------------------------------------

        # position (within this component) of the best node (by degree)
        max_odeg = -1
        main_node_local_index = None
        for position, vertex_id in enumerate(component):
            this_odeg = odegs[vertex_id]
            if this_odeg > max_odeg:
                main_node_local_index = position
                max_odeg = this_odeg

        # we set it aside in our translated version our_comp
        main_node = our_comp.pop(main_node_local_index)

        # and unnest the others
        for remaining_id in our_comp:
            new_links.append((main_node, remaining_id))

    return new_links
