from gargantext.util.http import *
from gargantext.util.db import *
from gargantext.util.db_cache import cache
from gargantext.models import *
from gargantext.constants import *
from gargantext.settings import *

from datetime import datetime


@requires_auth
def explorer(request, project_id, corpus_id):
    '''
    Graph explorer, also known as TinaWebJS, using SigmaJS.
    Nodes are ngrams (from title or abstract or journal name.
    Links represent proximity measure.
    '''

    # we pass our corpus
    corpus = cache.Node[corpus_id]

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
        },
    )



@requires_auth
def myGraphs(request, project_id, corpus_id):
    '''
    List all of my Graphs
    '''

    user = cache.User[request.user.id]
    # we pass our corpus
    corpus = cache.Node[corpus_id]

    # and the project just for project.id in corpusBannerTop
    project = cache.Node[project_id]

    coocs = corpus.children('COOCCURRENCES', order=True).all()
    
    coocs_count = dict()
    for cooc in coocs:
        cooc_nodes = session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id==cooc.id).count()
        coocs_count[cooc.id] = cooc_nodes

    return render(
        template_name = 'pages/corpora/myGraphs.html',
        request = request,
        context = {
            'debug'     : settings.DEBUG,
            'request'   : request,
            'user'      : request.user,
            'date'      : datetime.now(),
            'project'   : project,
            'resourcename' : resourcename(corpus),
            'corpus'    : corpus,
            'view'      : 'myGraph',
            'coocs'     : coocs,
            'coocs_count' : coocs_count
        },
    )

