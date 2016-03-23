from gargantext.util.http     import APIView, get_parameters, JsonHttpResponse,\
                                     ValidationException
from gargantext.util.db       import session, aliased
from gargantext.util.db_cache import cache
from gargantext.models        import Ngram, NodeNgram, NodeNodeNgram
from gargantext.util.lists    import Translations
from sqlalchemy               import desc
# from gargantext.constants import *
# from gargantext.util.validation import validate
# from collections import defaultdict


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



class List(APIView):
    """
    see already available API query api/nodes/<list_id>?fields[]=ngrams
    """
    pass

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
    HOST/api/ngramlists/family?corpus=2&glance=10
    HOST/api/ngramlists/family?mainlist=91&scoring=94
    HOST/api/ngramlists/family?mainlist=91&scoring=94&glance=10
    HOST/api/ngramlists/family?mainlist=91&stoplist=90&scoring=94
     etc.

    REST Parameters:
    "glance=20"
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
        mainlist = None
        scores_id = None
        groups_id = None
        secondary_lists = {'maplist':None, 'stoplist':None}

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
            mainlist = corpus.children('MAINLIST').first().id,
            groups_id = corpus.children('GROUPLIST').first().id
            secondary_lists['stoplist'] = corpus.children('STOPLIST').first().id
            secondary_lists['maplist']  = corpus.children('MAPLIST').first().id,

        # custom request: refers to each list individually
        # -------------------------------------------------
        elif "mainlist" in parameters and "scoring" in parameters:
            mainlist = parameters['mainlist']
            scores_id = parameters['scoring']
            groups_id = None
            if 'groups' in parameters:
                groups_id = parameters['scoring']
            for k in ['stoplist', 'maplist']:
                if k in parameters:
                    secondary_lists[k] = parameters[k]

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
        if "glance" in parameters:
            # glance <=> only mainlist AND only k top ngrams
            glance_limit = int(parameters['glance'])
            mainlist_query = _query_list(mainlist, details=True,
                                          pagination_limit = glance_limit,
                                          scoring_metric_id= scores_id)
        else:
            # infos for all ngrams
            mainlist_query = _query_list(mainlist, details=True,
                                          scoring_metric_id= scores_id)
            # and for the other lists (stop and map)
            for li in secondary_lists:
                li_elts = _query_list(secondary_lists[li], details=False
                                      ).all()
                listmembers[li] = {ng[0]:True for ng in li_elts}

            # and the groupings
            if groups_id:
                links = Translations(groups_id)
                linkinfo = links.groups

        # the output form
        ngraminfo = {}
        for ng in mainlist_query.all():
            ng_id   = ng[0]
            # id => [term, weight]
            ngraminfo[ng_id] = ng[1:]

        return JsonHttpResponse({
            'ngraminfos' : ngraminfo,
            'listmembers' : listmembers,
            'links' : linkinfo
        })
