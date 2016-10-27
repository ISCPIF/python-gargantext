from gargantext.util.http import *
from gargantext.util.db import *
from gargantext.util.db_cache import cache
from gargantext.models import *
from gargantext.constants import *
from gargantext.settings import *
from gargantext.constants import USER_LANG
from datetime import datetime
from gargantext.views.pages.main import get_user_params

@requires_auth
def explorer(request, project_id, corpus_id):
    '''
    Graph explorer, also known as TinaWebJS, using SigmaJS.
    Nodes are ngrams (from title or abstract or journal name.
    Links represent proximity measure.

    Data are received in RESTfull mode (see rest.py).
    '''

    # we pass our corpus
    corpus = cache.Node[corpus_id]

    # security check
    user = cache.User[request.user.id]
    node_user = get_node_user(user)
    if corpus is None:
        raise Http404()
    if not user.owns(corpus):
        return HttpResponseForbidden()

    # get the maplist_id for modifications
    maplist_id = corpus.children(typename="MAPLIST").first().id

    # and the project just for project.id in corpusBannerTop
    project = cache.Node[project_id]

    # rendered page : explorer.html
    return render(
        template_name = 'graphExplorer/explorer.html',
        request = request,
        context = {
            'debug'     : settings.DEBUG   ,
            'request'   : request          ,
            'user'      : request.user     ,
            'date'      : datetime.now()   ,
            'project'   : project          ,
            'corpus'    : corpus           ,
            'maplist_id': maplist_id       ,
            'view'      : 'graph'          ,
            'user_parameters': get_user_params(request.user),
            'languages': USER_LANG
        },
    )



@requires_auth
def myGraphs(request, project_id, corpus_id):
    '''
    List all of my Graphs.

    Each Graphs as one Node of Cooccurrences.
    Each Graph is save in hyperdata of each Node.
    '''

    user = cache.User[request.user.id]
    user_node = get_node_user(user)
    # we pass our corpus
    corpus = cache.Node[corpus_id]

    # and the project just for project.id in corpusBannerTop
    project = cache.Node[project_id]

    coocs = corpus.children('COOCCURRENCES', order=True).all()

    coocs_count = dict()
    for cooc in coocs:
        # FIXME : approximativ number of nodes (not exactly what user sees in explorer)
        # Need to be connected with Graph Clustering
        cooc_nodes = (session.query(Ngram.id,func.count(Ngram.id))
                             .join(NodeNgramNgram, NodeNgramNgram.ngram1_id == Ngram.id)
                             .filter(NodeNgramNgram.node_id==cooc.id)
                             .filter(NodeNgramNgram.weight >= 1)
                             .group_by(Ngram.id)
                             .all()
                     )

        #coocs_count[cooc.id] = len(cooc_nodes)
        coocs_count[cooc.id] = len([cooc_node for cooc_node in cooc_nodes if cooc_node[1] > 1])

        print("coocs_count a posteriori", coocs_count)

    return render(
        template_name = 'pages/corpora/myGraphs.html',
        request = request,
        context = {
            'debug'        : settings.DEBUG,
            'request'      : request,
            'user'         : request.user,
            'date'         : datetime.now(),
            'project'      : project,
            'resourcename' : get_resource_by_name(corpus),
            'corpus'       : corpus,
            'view'         : 'myGraph',
            'coocs'        : coocs,
            'coocs_count'  : coocs_count,
            'user_parameters': user_node.hyperdata,
            'languages': USER_LANG,
        },
    )
