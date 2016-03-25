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

    # and the project just for project.id in corpusBannerTop
    project = cache.Node[project_id]

    graphurl = "projects/" + str(project_id) + "/corpora/" + str(corpus_id) + "/node_link.json"
    
    # rendered page : journals.html
    return render(
        template_name = 'graphExplorer/explorer.html',
        request = request,
        context = {
            'debug'     : settings.DEBUG,
            'request'   : request,
            'user'      : request.user,
            'date'      : datetime.now(),
            'project'   : project,
            'corpus'    : corpus,
            #'list_id'   : maplist.id,\
            'graphfile' : graphurl,\
            'view'      : 'graph'
        },
    )

