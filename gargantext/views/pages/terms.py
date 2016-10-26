from gargantext.util.http     import requires_auth, render, settings
from gargantext.util.db       import session
from gargantext.util.db_cache import cache
from gargantext.models        import Node
from gargantext.constants     import get_resource
from datetime                 import datetime

def get_node_user(user):
    #load user parameters
    node_user = session.query(Node).filter(Node.user_id == user.id,  Node.typename== "USER").first()

    if node_user is None:
        node_user = Node(typename== "USER", user_id = user.id, name= user.name)
        #default language for now is  'fr'
        node_user["hyperdata"]["language"] = "fr"
        session.add(node_user)
        session.commit()
    return node_user

@requires_auth
def ngramtable(request, project_id, corpus_id):
    '''
    Browse and modify all lists together.
       => maplist and mainlist terms in a table
          with groupings as '+' nodes
       => uses API GET batch of lists
       => uses API PUT/DEL for list modifications
       => uses frontend AJAX through Ngrams_dyna_charts_and_table.js
    # TODO refactor Ngrams_dyna_charts_and_table.js
    '''
    # corpus still necessary to find all lists
    corpus = cache.Node[corpus_id]

    # and the project just for project.id in corpusBannerTop
    project = cache.Node[project_id]

    # retrieve all corpora of this user for list import option
    # POSSIBILITY: could do same task in ajax "only if needed"
    #              (use api for that when merged)
    corpora_infos_q = (session.query(Node.id, Node.name)
                              .filter(Node.typename == "CORPUS")
                              .filter(Node.user_id == project.user_id))
                               # .filter(Node.id != corpus_id)
    corpora_infos = corpora_infos_q.all()

    source_type = corpus.resources()[0]['type']
    user_node = get_node_user(request.user)
    # rendered page : terms.html
    return render(
        template_name = 'pages/corpora/terms.html',
        request = request,
        context = {
            'debug': settings.DEBUG,
            'user': request.user,
            'date': datetime.now(),
            'project': project,
            'corpus' : corpus,
            'resourcename' : get_resource(source_type)['name'],
            'view': 'terms',

            # for the CSV import modal
            'importroute': "/api/ngramlists/import?onto_corpus=%i"% corpus.id,
            'corporainfos' : corpora_infos,
            'user_parameters': user_node.hyperdata,
        },
    )
