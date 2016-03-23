from gargantext.util.http     import requires_auth, render, settings
from gargantext.util.db       import session
from gargantext.util.db_cache import cache
from gargantext.models        import Node
from datetime                 import datetime

@requires_auth
def ngramtable(request, project_id, corpus_id):
    '''
    Browse and modify all lists together.
       => maplist and mainlist terms in a table
          with groupings as '+' nodes
       => uses API GET batch of lists
       => uses API PUT/DEL for list modifications (TODO)
       => uses frontend AJAX through Ngrams_dyna_charts_and_table.js
    # TODO refactor Ngrams_dyna_charts_and_table.js
    '''
    # corpus still necessary to find all lists
    corpus = cache.Node[corpus_id]

    # and the project just for project.id in corpusBannerTop
    project = cache.Node[project_id]

    # rendered page : journals.html
    return render(
        template_name = 'pages/corpora/terms.html',
        request = request,
        context = {
            'debug': settings.DEBUG,
            'date': datetime.now(),
            'project': project,
            'corpus' : corpus,
            'view': 'terms'
        },
    )
