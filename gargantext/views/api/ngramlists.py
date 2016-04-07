"""
API views for advanced operations on ngrams and ngramlists
-----------------------------------------------------------
    - retrieve several lists together ("family")
    - retrieve detailed list infos (ngram_id, term strings, scores...)
    - modify NodeNgram lists (PUT/DEL an ngram to a MAINLIST OR MAPLIST...)
    - modify NodeNgramNgram groups (POST a list of groupings like {"767":[209,640],"779":[436,265,385]}")
"""

from gargantext.util.http     import APIView, get_parameters, JsonHttpResponse,\
                                     ValidationException, Http404
from gargantext.util.db       import session, aliased, desc, bulk_insert
from gargantext.util.db_cache import cache, or_
from gargantext.models        import Ngram, NodeNgram, NodeNodeNgram, NodeNgramNgram
from gargantext.util.lists    import UnweightedList, Translations


def _query_list(list_id,
                pagination_limit=None, pagination_offset=None,
                details=False, scoring_metric_id=None
                ):
    """
    Paginated listing of ngram_ids in a NodeNgram lists.

    Works for a mainlist or stoplist or maplist (not grouplists!)

    Parameter:
      - pagination_limit, pagination_offset
      - details: if False, send just the array of ngram_ids
                 if True, send triples with (ngram_id, term, scoring)
                                                             ^^^^^^^
      - scoring_metric_id: id of a scoring metric node   (TFIDF or OCCS)
                           (for details and sorting)
    """
    if not details:
        # simple contents
        query = session.query(NodeNgram.ngram_id)
    else:
        # detailed contents (terms and some NodeNodeNgram for score)
        query = (session
                    .query(
                        NodeNgram.ngram_id,
                        Ngram.terms,
                        NodeNodeNgram.score
                     )
                    .join(Ngram, NodeNgram.ngram_id == Ngram.id)
                    .join(NodeNodeNgram, NodeNgram.ngram_id == NodeNodeNgram.ngram_id)
                    .filter(NodeNodeNgram.node1_id == scoring_metric_id)
                    .order_by(desc(NodeNodeNgram.score))
                )

    # main filter
    # -----------
    query = query.filter(NodeNgram.node_id == list_id)

    if pagination_limit:
        query = query.limit(pagination_limit)

    if pagination_offset:
        query = query.offset(pagination_offsets)

    return query




def _query_grouped_ngrams(groupings_id, details=False, scoring_metric_id=None):
    """
    Listing of "hidden" ngram_ids from the groups

    Works only for grouplists

    Parameter:
      - details: if False, send just the array of ngram_ids
                 if True, send triples with (ngram_id, term, scoring)
                                                             ^^^^^^^
      - scoring_metric_id: id of a scoring metric node   (TFIDF or OCCS)
                           (for details and sorting)
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
                        NodeNodeNgram.score
                     )
                    .join(Ngram, NodeNgramNgram.ngram2_id == Ngram.id)
                    .join(NodeNodeNgram, NodeNgramNgram.ngram2_id == NodeNodeNgram.ngram_id)
                    .filter(NodeNodeNgram.node1_id == scoring_metric_id)
                    .order_by(desc(NodeNodeNgram.score))
                )

    # main filter
    # -----------
    query = query.filter(NodeNgramNgram.node_id == groupings_id)

    return query

class List(APIView):
    """
    see already available API query api/nodes/<list_id>?fields[]=ngrams
    """
    pass


class GroupChange(APIView):
    """
    Modification of some groups
    (typically new subform nodes under a mainform)

    USAGE EXEMPLE:
    HOST/api/ngramlists/groups?node=43
                                vvvvvv
                               group node
                               to modify

    We use POST HTTP method to send group data with structure like:
     {
        mainform_A: [subform_A1],
        mainformB:  [subform_B1,subform_B2,subform_B3]
        ...
     }

    Chained effect:

    NB: request.user is also checked for current authentication status
    """

    def initial(self, request):
        """
        Before dispatching to post()

        Checks current user authentication to prevent remote DB manipulation
        """
        if not request.user.is_authenticated():
            raise Http404()
            # can't use return in initial() (although 401 maybe better than 404)
            # can't use @requires_auth because of positional 'self' within class

    def post(self, request):
        """
        Rewrites the group node **selectively**

          => removes couples where newly reconnected ngrams where involved
          => adds new couples from GroupsBuffer of terms view

        TODO see use of util.lists.Translations
        TODO benchmark selective delete compared to entire list rewrite
        """
        group_node = get_parameters(request)['node']
        all_nodes_involved = []
        links = []

        print([i for i in request.POST.lists()])
        pass


        for (mainform_key, subforms_ids) in request.POST.lists():
            mainform_id = mainform_key[:-2]   # remove brackets '543[]' -> '543'
            all_nodes_involved.append(mainform_id)
            for subform_id in subforms_ids:
                links.append((mainform_id,subform_id))
                all_nodes_involved.append(subform_id)

        # remove selectively all groupings with these nodes involved
        # TODO benchmark
        old_links = (session.query(NodeNgramNgram)
                    .filter(NodeNgramNgram.node_id == group_node)
                    .filter(or_(
                            NodeNgramNgram.ngram1_id.in_(all_nodes_involved),
                            NodeNgramNgram.ngram2_id.in_(all_nodes_involved)))
                )
        n_removed = old_links.count()
        old_links.delete(synchronize_session='fetch')
        print('n_removed', n_removed)
        print("links", links)
        print(
            [i for i in ((group_node, mainform, subform, 1.0) for (mainform,subform) in links)]
            )
        bulk_insert(
            NodeNgramNgram,
            ('node_id', 'ngram1_id', 'ngram2_id', 'weight'),
            ((group_node, mainform, subform, 1.0) for (mainform,subform) in links)
        )

        return JsonHttpResponse({
            'count_removed': n_removed,
            'count_added': len(links),
            }, 200)




class ListChange(APIView):
    """
    Any ngram action on standard NodeNgram lists (MAIN, MAP, STOP)

    USAGE EXEMPLE:
    HOST/api/ngramlists/change?list=42&ngrams=1,2,3,4,5
                                vvvvvv          ||||||
                               old list         vvvvvv
                               to modify     new list items
                                  |                |
                                  v                v
     2 x UnweightedLists:   self.base_list   self.change_list

    We use DEL/PUT HTTP methods to differentiate the 2 basic rm/add actions
    They rely only on inline parameters (no need for payload data)

    No chained effects: eg removing from MAPLIST will not remove
                          automatically from associated MAINLIST

    NB: request.user is also checked for current authentication status
    """

    def initial(self, request):
        """
        Before dispatching to put(), delete()...

        1) Checks current user authentication to prevent remote DB manipulation
        2) Prepares self.list_objects from params
        """
        if not request.user.is_authenticated():
            raise Http404()
            # can't use return in initial() (although 401 maybe better than 404)
            # can't use @requires_auth because of positional 'self' within class

        # get validated params
        self.params = get_parameters(request)
        (self.base_list, self.change_list) = ListChange._validate(self.params)

    def put(self, request):
        """
        Adds one or more ngrams to a list.
        """
        # union of items ----------------------------
        new_list = self.base_list + self.change_list
        # -------------------------------------------

        # save
        new_list.save(self.base_list.id)

        return JsonHttpResponse({
            'parameters': self.params,
            'count_added': len(new_list.items) - len(self.base_list.items),
        }, 201)

    def delete(self, request):
        """
        Removes one or more ngrams from a list.
        """
        # removal (set difference) ------------------
        new_list = self.base_list - self.change_list
        # -------------------------------------------

        # save
        new_list.save(self.base_list.id)

        return JsonHttpResponse({
            'parameters': self.params,
            'count_removed': len(self.base_list.items) - len(new_list.items),
        }, 200)

    @staticmethod
    def _validate(params):
        """
        Checks "list" and "ngrams" parameters for their:
          - presence
          - type

        These two parameters are mandatory for any ListChange methods.

        ngrams are also converted to an UnweightedList object for easy add/remove
        """
        if 'list' not in params:
            raise ValidationException('The route /api/ngramlists/change requires a "list" \
                                       parameter, for instance /api/ngramlists/change?list_id=42')
        if 'ngrams' not in params:
            raise ValidationException('The route /api/ngramlists/change requires an "ngrams"\
                                       parameter, for instance /api/ngramlists/change?ngrams=1,2,3,4')

        # 2 x retrieval => 2 x UnweightedLists
        # ------------------------------------
        base_list_id = None
        try:
            base_list_id = int(params['list'])
            # UnweightedList retrieved by id
            base_list = UnweightedList(base_list_id)
        except:
            raise ValidationException('The "list" parameter requires an existing list id.')

        change_ngram_ids = []
        try:
            change_ngram_ids = [int(n) for n in params['ngrams'].split(',')]
            # UnweightedList created from items
            change_list = UnweightedList(change_ngram_ids)
        except:
            raise ValidationException('The "ngrams" parameter requires one or more ngram_ids separated by comma')

        return(base_list, change_list)


class ListFamily(APIView):
    """
    Compact combination of *multiple* list info
        custom made for the "terms" view
    ---
    Sends all JSON info of a collection of the 4 list types of a corpus
    (or for any combination of lists that go together):
      - a mainlist
      - an optional stoplist
      - an optional maplist
      - an optional grouplist

    USAGE EXEMPLES
    HOST/api/ngramlists/family?corpus=2
    HOST/api/ngramlists/family?corpus=2&head=10
    HOST/api/ngramlists/family?mainlist=91&scoring=94
    HOST/api/ngramlists/family?mainlist=91&scoring=94&head=10
    HOST/api/ngramlists/family?mainlist=91&stoplist=90&scoring=94
     etc.

    REST Parameters:
    "head=20"
        use pagination to only load the k top ngrams of the mainlist
        (useful for fast loading of terms view)
    "corpus=ID"
        the corpus id to retrieve all 4 lists
    "scoring=ID"
        the scoring node (defaults to the OCCURRENCES child of the corpus)
    "mainlist=ID&scoring=ID[&stoplist=ID&groups=ID&maplist=ID]"
        alternative call syntax without specifying a corpus
        (uses all explicit IDs of the lists => gives the possibility for custom term views)
    """
    def get(self, request):

        parameters = get_parameters(request)
        glance_limit = None
        mainlist_id = None
        scores_id = None
        groups_id = None
        other_list_ids = {'maplist':None, 'stoplist':None}

        # 1) retrieve a mainlist_id and other lists
        ##########################################

        # simple request: just refers to the parent corpus
        # ------------------------------------------------
        if "corpus" in parameters:
            corpus_id = parameters['corpus']
            corpus = cache.Node[corpus_id]
            # with a corpus_id, the explicit scoring pointer is optional
            if "scoring" in parameters:
                scores_id = parameters['scoring']
            else:
                scores_id = corpus.children('OCCURRENCES').first().id
            # retrieve the family of lists that have corpus as parent
            mainlist_id = corpus.children('MAINLIST').first().id
            groups_id = corpus.children('GROUPLIST').first().id
            other_list_ids['stoplist'] = corpus.children('STOPLIST').first().id
            other_list_ids['maplist']  = corpus.children('MAPLIST').first().id

        # custom request: refers to each list individually
        # -------------------------------------------------
        elif "mainlist" in parameters and "scoring" in parameters:
            mainlist_id = parameters['mainlist']
            scores_id = parameters['scoring']
            groups_id = None
            if 'groups' in parameters:
                groups_id = parameters['scoring']
            for k in ['stoplist', 'maplist']:
                if k in parameters:
                    other_list_ids[k] = parameters[k]

        # or request has an error
        # -----------------------
        else:
            raise ValidationException(
                "Either a 'corpus' parameter or 'mainlist' & 'scoring' params are required"
                )


        # 2) get the infos for each list
        ################################
        ngraminfo = {}           # ngram details sorted per ngram id
        linkinfo  = {}           # ngram groups sorted per ngram id
        listmembers = {}         # ngram ids sorted per list name
        if "head" in parameters:
            # head <=> only mainlist AND only k top ngrams
            glance_limit = int(parameters['head'])
            mainlist_query = _query_list(mainlist_id, details=True,
                                          pagination_limit = glance_limit,
                                          scoring_metric_id= scores_id)
        else:
            # infos for all ngrams from mainlist
            mainlist_query = _query_list(mainlist_id, details=True,
                                          scoring_metric_id= scores_id)
            # infos for grouped ngrams, absent from mainlist
            hidden_ngrams_query = _query_grouped_ngrams(groups_id, details=True,
                                          scoring_metric_id= scores_id)

            # and for the other lists (stop and map)
            # no details needed here, just the member ids
            #   - maplist ngrams will already be in ngraminfos b/c of mainlist
            #   - stoplist ngrams will not be shown in detail
            for li in other_list_ids:
                li_elts = _query_list(other_list_ids[li], details=False
                                      ).all()
                # simple array of ngram_ids
                listmembers[li] = [ng[0] for ng in li_elts]

            # and the groupings
            if groups_id:
                links = Translations(groups_id)
                linkinfo = links.groups

        # the output form
        for ng in mainlist_query.all() + hidden_ngrams_query.all():
            ng_id   = ng[0]
            # id => [term, weight]
            ngraminfo[ng_id] = ng[1:]

            # NB the client js will sort mainlist ngs from hidden ngs after ajax
            #    using linkinfo (otherwise needs redundant listmembers for main)

        return JsonHttpResponse({
            'ngraminfos' : ngraminfo,
            'listmembers' : listmembers,
            'links' : linkinfo,
            'nodeids' : {
                'mainlist':  mainlist_id,
                'maplist' :  other_list_ids['maplist'],
                'stoplist':  other_list_ids['stoplist'],
                'groups':  groups_id,
                'scores':  scores_id,
            }
        })
