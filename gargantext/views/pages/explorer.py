from gargantext.util.http import *
from gargantext.util.db import *
from gargantext.util.db_cache import cache
from gargantext.models import *
from gargantext.constants import *
from gargantext.settings import *

from datetime import datetime


@requires_auth
def graph(request, project_id, corpus_id):
    '''
    Graph explorer, also known as TinaWebJS, using SigmaJS.
    Nodes are ngrams (from title or abstract or journal name.
    Links represent proximity measure.
    '''

    # we pass our corpus
    corpus = cache.Node[corpus_id]
    
    # we pass our user_id
    #user_id         = corpus.user_id

    # and the project just for project.id in corpusBannerTop
    project = cache.Node[project_id]
    
    #miamlist_type_id = cache.NodeType['MiamList'].id

    graphurl = "projects/" + str(project_id) + "/corpora/" + str(corpus_id) + "/node_link.json"
    
    # rendered page : journals.html
    return render(
        template_name = 'pages/graph.html',
        request = request,
        context = {
            'debug'     : settings.DEBUG,
            # 'user' : user_id,
            'date'      : datetime.now(),
            'project'   : project,
            'corpus'    : corpus,
            #'list_id'   : maplist.id,\
            'graphfile' : graphurl,\
            'view'      : 'graph'
        },
    )




