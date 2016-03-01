from gargantext.util.http import *
from gargantext.util.db import *
from gargantext.util.db_cache import cache
from gargantext.models import *
from gargantext.constants import *
from gargantext.settings import *

from datetime import datetime


def _get_user_project_corpus(request, project_id, corpus_id):
    """Helper method to get a corpus, knowing the project's and corpus' ID.
    Raises HTTP errors when parameters (user, IDs...) are invalid.
    """
    user = cache.User[request.user.id]
    project = session.query(Node).filter(Node.id == project_id).first()
    corpus = session.query(Node).filter(Node.id == corpus_id).filter(Node.parent_id == project_id).first()
    if corpus is None:
        raise Http404()
    if not user.owns(corpus):
        print("CORPORA: invalid user %i (User doesn't own this corpus)" % user.id)
        return (False, user, project, corpus)
    return (True, user, project, corpus)


@requires_auth
def corpus(request, project_id, corpus_id):
    authorized, user, project, corpus = _get_user_project_corpus(request, project_id, corpus_id)
    if not authorized:
        return HttpResponseForbidden()
    # response!
    return render(
        template_name = 'pages/corpora/corpus.html',
        request = request,
        context = {
            'debug': DEBUG,
            'user': user,
            'date': datetime.now(),
            'project': project,
            'corpus': corpus,
            # 'processing': corpus['extracted'],
            # 'number': number,
            'view': 'documents'
        },
    )

@requires_auth
def chart(request, project_id, corpus_id):
    user, project, corpus = _get_user_project_corpus(request, project_id, corpus_id)
