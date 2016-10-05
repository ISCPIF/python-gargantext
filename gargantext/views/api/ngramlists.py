"""
API views for advanced operations on ngrams and ngramlists
-----------------------------------------------------------
    - retrieve several lists together ("family")
    - retrieve detailed list infos (ngram_id, term strings, scores...)
    - modify NodeNgram lists (PUT/DEL an ngram to a MAINLIST OR MAPLIST...)
    - modify NodeNgramNgram groups (PUT/DEL a list of groupings like {"767[]":[209,640],"779[]":[436,265,385]}")
"""

from gargantext.util.http     import APIView, get_parameters, JsonHttpResponse,\
                                     ValidationException, Http404, HttpResponse
from gargantext.util.db       import session, aliased, bulk_insert
from gargantext.util.db_cache import cache
from sqlalchemy               import tuple_
from gargantext.models        import Ngram, NodeNgram, NodeNodeNgram, NodeNgramNgram, Node
from gargantext.util.lists    import UnweightedList, Translations

# useful subroutines
from gargantext.util.ngramlists_tools import query_list, export_ngramlists, \
                                             import_ngramlists, merge_ngramlists, \
                                             import_and_merge_ngramlists
from gargantext.util.group_tools      import query_grouped_ngrams


class List(APIView):
    """
    see already available API query api/nodes/<list_id>?fields[]=ngrams
    """
    pass


class CSVLists(APIView):
    """
    GET   => CSV exports of all lists of a corpus

    POST  => CSV import into existing lists as "post"
    PATCH => internal import into existing lists (?POSSIBILITY put it in another class ?)
    """
    def get(self, request):
        params = get_parameters(request)
        corpus_id = int(params.pop("corpus"))
        corpus_node = cache.Node[corpus_id]

        # response is file-like + headers
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="corpus-%i_gargantext_term_list.csv"' % corpus_id

        # fill the response with the data
        export_ngramlists(corpus_node, fname=response, titles=True)
        return response


    def post(self,request):
        """
        Merge the lists of a corpus with other lists from a CSV source
                                                 or from another corpus

        params in request.GET:
            onto_corpus:  the corpus whose lists are getting patched

        params in request.data:
            csvfile:      the csv file

        /!\ We assume we checked the file size client-side before upload
        """
        if not request.user.is_authenticated():
            res = HttpResponse("Unauthorized")
            res.status_code = 401
            return res

        # the corpus with the target lists to be patched
        params = get_parameters(request)
        corpus_id = int(params.pop("onto_corpus"))
        corpus_node = cache.Node[corpus_id]

        if request.user.id != corpus_node.user_id:
            res = HttpResponse("Unauthorized")
            res.status_code = 401
            return res

        # request also contains the file
        # csv_file has type django.core.files.uploadedfile.InMemoryUploadedFile
        #                                                 ----------------------
        csv_file = request.data['csvfile']

        csv_contents = csv_file.read().decode("UTF-8").split("\n")
        csv_file.close()
        del csv_file

        # import the csv
        # try:
        log_msg = import_and_merge_ngramlists(csv_contents,
                                              onto_corpus_id = corpus_node.id)
        return JsonHttpResponse({
            'log': log_msg,
            }, 200)

        # except Exception as e:
        #     return JsonHttpResponse({
        #         'err': str(e),
        #         }, 400)

    def patch(self,request):
        """
        A copy of POST (merging list) but with the source == just an internal corpus_id

        params in request.GET:
            onto_corpus:  the corpus whose lists are getting patched
            from:         the corpus from which we take the source lists to merge in
            todo:         an array of the list types ("map", "main", "stop") to merge in

        """
        if not request.user.is_authenticated():
            res = HttpResponse("Unauthorized")
            res.status_code = 401
            return res

        params = get_parameters(request)
        print(params)

        # the corpus with the target lists to be patched
        corpus_id = int(params.pop("onto_corpus"))
        corpus_node = cache.Node[corpus_id]

        print(params)

        if request.user.id != corpus_node.user_id:
            res = HttpResponse("Unauthorized")
            res.status_code = 401
            return res

        list_types = {'map':'MAPLIST', 'main':'MAINLIST', 'stop':'STOPLIST'}

        # internal DB retrieve source_lists
        source_corpus_id = int(params.pop("from_corpus"))
        source_node = cache.Node[source_corpus_id]

        todo_lists = params.pop("todo").split(',')   # ex: ['map', 'stop']
        source_lists = {}
        for key in todo_lists:
            source_lists[key] = UnweightedList(
                                    source_node.children(list_types[key]).first().id
                                )

        # add the groupings too
        source_lists['groupings'] = Translations(
                                        source_node.children("GROUPLIST").first().id
                                    )

        # attempt to merge and send response
        try:
            # merge the source_lists onto those of the target corpus
            log_msg = merge_ngramlists(source_lists, onto_corpus=corpus_node)
            return JsonHttpResponse({
                'log': log_msg,
                }, 200)

        except Exception as e:
            return JsonHttpResponse({
                'err': str(e),
                }, 400)



class GroupChange(APIView):
    """
    Modification of some groups
    (typically new subform nodes under a mainform)

    USAGE EXEMPLE:
    HOST/api/ngramlists/groups?node=43
                                vvvvvv
                               group node
                               to modify

    We use PUT HTTP method to send group data to DB and DELETE to remove them.

    They both use same data format in the url (see links_to_couples).

    No chained effects : simply adds or deletes rows of couples

    NB: request.user is also checked for current authentication status
    """

    def initial(self, request):
        """
        Before dispatching to post() or delete()

        Checks current user authentication to prevent remote DB manipulation
        """
        if not request.user.is_authenticated():
            raise Http404()
            # can't use return in initial() (although 401 maybe better than 404)
            # can't use @requires_auth because of positional 'self' within class

    def links_to_couples(self,params):
        """
        IN (dict from url params)
        ---
        params = {
                       "mainform_A": ["subform_A1"]
                       "mainform_B": ["subform_B1,subform_B2,subform_B3"]
                       ...
                     }

        OUT (for DB rows)
        ----
        couples = [
                    (mainform_A , subform_A1),
                    (mainform_B , subform_B1),
                    (mainform_B , subform_B2),
                    (mainform_B , subform_B3),
                    ...
                  ]
        """
        couples = []
        for (mainform_id, subforms_ids) in params.items():
            for subform_id in subforms_ids[0].split(','):
                # append the couple
                couples.append((int(mainform_id),int(subform_id)))
        return couples

    def put(self, request):
        """
        Add some group elements to a group node
          => adds new couples from GroupsBuffer._to_add of terms view

        TODO see use of util.lists.Translations

        Parameters are all in the url (for symmetry with DELETE method)
           api/ngramlists/groups?node=783&1228[]=891,1639
                                     => creates 1228 - 891
                                            and 1228 - 1639

        general format is:   mainform_id[]=subform_id1,subform_id2 etc
                                     => creates mainform_id - subform_id1
                                            and mainform_id - subform_id2

        NB: also checks if the couples exist before because the ngram table
            will send the entire group (old existing links + new links)
        """
        # from the url
        params = get_parameters(request)
        # the node param is unique
        group_node = params.pop('node')
        # the others params are links to change
        couples = self.links_to_couples(params)

        # debug
        # print("==couples from url =================================++++=")
        # print(couples)

        # local version of "insert if not exists" -------------------->8--------
        # (1) check already existing elements
        check_query = (session.query(NodeNgramNgram)
                        .filter(NodeNgramNgram.node_id == group_node)
                        .filter(
                            tuple_(NodeNgramNgram.ngram1_id, NodeNgramNgram.ngram2_id)
                            .in_(couples)
                    )
                )

        existing = {}
        for synonyms in check_query.all():
            existing[(synonyms.ngram1_id,synonyms.ngram2_id)] = True

        # debug
        #print("==existing")
        #print(existing)

        # (2) compute difference locally
        couples_to_add = [(mform,sform) for (mform,sform)
                                        in couples
                                        if (mform,sform) not in existing]

        # debug
        # print("== couples_to_add =================================++++=")
        # print(couples_to_add)


        # (3) add new groupings
        bulk_insert(
            NodeNgramNgram,
            ('node_id', 'ngram1_id', 'ngram2_id', 'weight'),
            ((group_node, mainform, subform, 1.0) for (mainform,subform)
                                                  in couples_to_add)
        )

        # ------------------------------------------------------------>8--------

        return JsonHttpResponse({
            'count_added': len(couples_to_add),
            }, 200)



    def delete(self, request):
        """
        Within a groupnode, deletes some group elements from some groups

        Data format just like in POST, everything in the url
        """

        # from the url
        params = get_parameters(request)
        # the node param is unique
        group_node = params.pop('node')
        # the others params are links to change
        couples_to_remove = self.links_to_couples(params)

        # debug
        # print("==couples_to_remove=================================dd=")
        # print(couples_to_remove)

        # remove selectively group_couples
        # using IN is correct in this case: list of ids is short and external
        # see stackoverflow.com/questions/444475/
        db_rows = (session.query(NodeNgramNgram)
                    .filter(NodeNgramNgram.node_id == group_node)
                    .filter(
                      tuple_(NodeNgramNgram.ngram1_id, NodeNgramNgram.ngram2_id)
                      .in_(couples_to_remove)
                    )
                )

        n_removed = db_rows.delete(synchronize_session=False)
        session.commit()

        return JsonHttpResponse({
            'count_removed': n_removed
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

        if not len(self.change_list.items):
            payload_ngrams = request.data['ngrams']
            # print("no change_list in params but we got:", payload_ngrams)
            # change_list can be in payload too
            change_ngram_ids = [int(n) for n in payload_ngrams.split(',')]
            if (not len(change_ngram_ids)):
                raise ValidationException('The "ngrams" parameter requires one or more ngram_ids separated by comma')
            else:
                self.change_list = UnweightedList(change_ngram_ids)


    def put(self, request):
        """
        Adds one or more ngrams to a list.

        NB: we assume ngram_ids don't contain subforms !!
            (this assumption is not checked here because it would be
             slow: if you want to add a subform, send the mainform's id)
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
        # if 'ngrams' not in params:
        #     raise ValidationException('The route /api/ngramlists/change requires an "ngrams"\
        #                                parameter, for instance /api/ngramlists/change?ngrams=1,2,3,4')

        # 2 x retrieval => 2 x UnweightedLists
        # ------------------------------------
        base_list_id = None
        try:
            base_list_id = int(params['list'])
            # UnweightedList retrieved by id
        except:
            raise ValidationException('The "list" parameter requires an existing list id.')
        base_list = UnweightedList(base_list_id)

        change_ngram_ids = []
        try:
            change_ngram_ids = [int(n) for n in params['ngrams'].split(',')]
            # UnweightedList created from items
        except:
            # ngrams no longer mandatory inline, see payload check afterwards
            pass
        change_list = UnweightedList(change_ngram_ids)

        return(base_list, change_list)


class MapListGlance(APIView):
    """
    Fast infos about the maplist only

    HOST/api/ngramlists/glance?corpus=2
    HOST/api/ngramlists/glance?maplist=92

    REST Parameters:
    "maplist=92"
        the maplist to retrieve
    "corpus=ID"
        alternatively, the corpus to which the maplist belongs
    """

    def get(self, request):
        parameters = get_parameters(request)

        maplist_id = None
        scores_id = None

        if "corpus" in parameters:
            corpus_id = parameters['corpus']
            corpus = cache.Node[corpus_id]
            maplist_id = corpus.children('MAPLIST').first().id
            # with a corpus_id, the explicit scoring pointer is optional
            if "scoring" in parameters:
                scores_id = parameters['scoring']
            else:
                scores_id = corpus.children('OCCURRENCES').first().id

        elif "maplist" in parameters and "scoring" in parameters:
            maplist_id = int(parameters['mainlist'])
            scores_id = int(parameters['scoring'])
        else:
            raise ValidationException("A 'corpus' id or 'maplist' id is required, and a 'scoring' for occurences counts")

        ngraminfo = {}           # ngram details sorted per ngram id
        listmembers = {'maplist':[]}         # ngram ids sorted per list name

        # infos for all ngrams from maplist
        map_ngrams = query_list(maplist_id, details=True,
                                      scoring_metric_id= scores_id).all()

        # ex:  [(8805, 'mean age', 4.0),
        #        (1632, 'activity', 4.0),
        #        (8423, 'present', 2.0),
        #        (2928, 'objective', 2.0)]


        # shortcut to useful function during loop
        add_to_members = listmembers['maplist'].append

        for ng in map_ngrams:
            ng_id   = ng[0]
            ngraminfo[ng_id] = ng[1:]

            # maplist ngrams will already be <=> ngraminfos
            # but the client side expects a membership lookup
            # as when there are multiple lists or some groupings
            add_to_members(ng_id)


        return JsonHttpResponse({
            'ngraminfos' : ngraminfo,
            'listmembers' : listmembers,
            'links' : {},   # no grouping links sent during glance (for speed)
            'nodeids' : {
                'mainlist':  None,
                'maplist' :  maplist_id,
                'stoplist':  None,
                'groups':  None,
                'scores':  None,
            }
        })



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
        (useful for fast loading of terms view) [CURRENTLY NOT USED]
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
            mainlist_query = query_list(mainlist_id, details=True,
                                          pagination_limit = glance_limit,
                                          scoring_metric_id= scores_id)
        else:
            # infos for all ngrams from mainlist
            mainlist_query = query_list(mainlist_id, details=True,
                                          scoring_metric_id= scores_id)
            # infos for grouped ngrams, absent from mainlist
            hidden_ngrams_query = query_grouped_ngrams(groups_id, details=True)

            # infos for stoplist terms, absent from mainlist
            stop_ngrams_query = query_list(other_list_ids['stoplist'], details=True,
                                            scoring_metric_id=scores_id)

            # and for the other lists (stop and map)
            # no details needed here, just the member ids
            for li in other_list_ids:
                li_elts = query_list(other_list_ids[li], details=False
                                      ).all()
                # simple array of ngram_ids
                listmembers[li] = [ng[0] for ng in li_elts]

            # and the groupings
            if groups_id:
                links = Translations(groups_id)
                linkinfo = links.groups

        # list of
        ngrams_which_need_detailed_info = []
        if "head" in parameters:
            # head triggered simplified form: just the top of the mainlist
            # TODO add maplist membership
            ngrams_which_need_detailed_info = mainlist_query.all()
        else:
            ngrams_which_need_detailed_info = mainlist_query.all() + hidden_ngrams_query.all() + stop_ngrams_query.all()

        # the output form of details is:
        # ngraminfo[id] => [term, weight]
        for ng in ngrams_which_need_detailed_info:
            ng_id   = ng[0]
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
