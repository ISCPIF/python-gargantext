from gargantext.util.db_cache   import cache
from gargantext.util.http       import ValidationException, APIView \
                                     , HttpResponse, JsonHttpResponse
from gargantext.util.toolchain.main import recount
from gargantext.util.scheduling import scheduled
from datetime                   import datetime

class CorpusMetrics(APIView):

    def patch(self, request, corpusnode_id):
        """
        PATCH triggers recount of metrics for the specified corpus.

        ex PATCH http://localhost:8000/api/metrics/14072
                                                   -----
                                                 corpus_id
        """
        print("==> update metrics request on ", corpusnode_id)

        if not request.user.is_authenticated():
            # can't use @requires_auth because of positional 'self' within class
            return HttpResponse('Unauthorized', status=401)

        try:
            corpus = cache.Node[int(corpusnode_id)]
        except:
            corpus = None

        if corpus is None:
            raise ValidationException("%s is not a valid corpus node id."
                                        % corpusnode_id)

        else:
            t_before = datetime.now()
            # =============
            scheduled(recount)(corpus.id)
            # =============
            t_after = datetime.now()

            return JsonHttpResponse({
                'corpus_id' : corpusnode_id,
                'took': "%f s." % (t_after - t_before).total_seconds()
            })
