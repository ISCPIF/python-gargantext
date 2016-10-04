from gargantext.util.http       import ValidationException, APIView \
                                     , get_parameters, JsonHttpResponse\
                                     , HttpResponse
from gargantext.util.db         import session, func
from gargantext.util.db_cache   import cache
from gargantext.models          import Node, Ngram, NodeNgram, NodeNgramNgram
from sqlalchemy.orm             import aliased
from re                         import findall

# ngrams put() will implement same text cleaning procedures as toolchain
from gargantext.util.toolchain.parsing           import normalize_chars
from gargantext.util.toolchain.ngrams_extraction import normalize_forms

# for indexing
from gargantext.util.toolchain.ngrams_addition  import index_new_ngrams


class ApiNgrams(APIView):

    def get(self, request):
        """
        Used for analytics
        ------------------

        Get ngram listing + counts in a given scope
        """
        # parameters retrieval and validation
        startwith = request.GET.get('startwith', '').replace("'", "\\'")

        # query ngrams
        ParentNode = aliased(Node)
        ngrams_query = (session
            .query(Ngram.id, Ngram.terms, func.sum(NodeNgram.weight).label('count'))
            .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
            .join(Node, Node.id == NodeNgram.node_id)
            .group_by(Ngram.id, Ngram.terms)
            # .group_by(Ngram)
            .order_by(func.sum(NodeNgram.weight).desc(), Ngram.terms)
        )

        # filters
        if 'startwith' in request.GET:
            ngrams_query = ngrams_query.filter(Ngram.terms.startswith(request.GET['startwith']))
        if 'contain' in request.GET:
            print("request.GET['contain']")
            print(request.GET['contain'])
            ngrams_query = ngrams_query.filter(Ngram.terms.contains(request.GET['contain']))
        if 'corpus_id' in request.GET:
            corpus_id_list = list(map(int, request.GET.get('corpus_id', '').split(',')))
            if corpus_id_list and corpus_id_list[0]:
                ngrams_query = ngrams_query.filter(Node.parent_id.in_(corpus_id_list))
        if 'ngram_id' in request.GET:
            ngram_id_list = list(map(int, request.GET.get('ngram_id', '').split(',')))
            if ngram_id_list and ngram_id_list[0]:
                ngrams_query = ngrams_query.filter(Ngram.id.in_(ngram_id_list))

        # pagination
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 20))
        total = ngrams_query.count()
        # return formatted result
        return JsonHttpResponse({
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': total,
            },
            'data': [
                {
                    'id': ngram.id,
                    'terms': ngram.terms,
                    'count': ngram.count,
                }
                for ngram in ngrams_query[offset : offset+limit]
            ],
        })


    def put(self, request):
        """
        Basic external access for *creating an ngram*
        ---------------------------------------------

         1 - checks user authentication before any changes

         2 - checks if ngram to Ngram table in DB
              if yes returns ngram_id and optionally mainform_id
              otherwise continues

         3 - adds the ngram to Ngram table in DB

         4 - (if corpus param is present)
             adds the ngram doc counts to NodeNgram table in DB
             (aka "index the ngram" throught the docs of the corpus)

         5 - returns json with:
             'msg'   => a success msg
             'text'  => the initial text content
             'term'  => the normalized text content
             'id'    => the new ngram_id
             'count' => the number of docs with the ngram in the corpus
                        (if corpus param is present)
             'group' => the mainform_id if applicable

        possible inline parameters
        --------------------------
        @param    text=<ngram_string>         [required]
        @param    corpus=<CORPUS_ID>          [optional]
        @param    testgroup (true if present) [optional, requires corpus]
        """

        # 1 - check user authentication
        if not request.user.is_authenticated():
            res = HttpResponse("Unauthorized")
            res.status_code = 401
            return res

        # the params
        params = get_parameters(request)

        print("PARAMS", [(i,v) for (i,v) in params.items()])

        if 'text' in params:
            original_text = str(params.pop('text'))
            ngram_str = normalize_forms(normalize_chars(original_text))
        else:
            raise ValidationException('The route PUT /api/ngrams/ is used to create a new ngram\
                                        It requires a "text" parameter,\
                                        for instance /api/ngrams?text=hydrometallurgy')

        if ('testgroup' in params) and (not ('corpus' in params)):
            raise ValidationException("'testgroup' param requires 'corpus' param")

        # if we have a 'corpus' param (to do the indexing)...
        do_indexation = False
        if 'corpus' in params:
            # we retrieve the corpus...
            corpus_id = int(params.pop('corpus'))
            corpus_node = cache.Node[corpus_id]
            # and the user must also have rights on the corpus
            if request.user.id == corpus_node.user_id:
                do_indexation = True
            else:
                res = HttpResponse("Unauthorized")
                res.status_code = 401
                return res

        # number of "words" in the ngram
        ngram_size = len(findall(r' +', ngram_str)) + 1

        # do the additions
        try:
            log_msg = ""
            ngram_id = None
            mainform_id = None

            preexisting = session.query(Ngram).filter(Ngram.terms==ngram_str).first()

            if preexisting is not None:
                ngram_id = preexisting.id
                log_msg += "ngram already existed (id %i)\n" % ngram_id

                # in the context of a corpus we can also check if has mainform
                # (useful for)
                if 'testgroup' in params:
                    groupings_id = (session.query(Node.id)
                                           .filter(Node.parent_id == corpus_id)
                                           .filter(Node.typename == 'GROUPLIST')
                                           .first()
                                    )
                    had_mainform = (session.query(NodeNgramNgram.ngram1_id)
                                          .filter(NodeNgramNgram.node_id == groupings_id)
                                          .filter(NodeNgramNgram.ngram2_id == preexisting.id)
                                          .first()
                                    )
                    if had_mainform:
                        mainform_id = had_mainform[0]
                        log_msg += "ngram had mainform (id %i) in this corpus" % mainform_id
                    else:
                        log_msg += "ngram was not in any group for this corpus"

            else:
                # 2 - insert into Ngrams
                new_ngram = Ngram(terms=ngram_str, n=ngram_size)
                session.add(new_ngram)
                session.commit()
                ngram_id = new_ngram.id
                log_msg += "ngram was added with new id %i\n" % ngram_id

            # 3 - index the term
            if do_indexation:
                n_added = index_new_ngrams([ngram_id], corpus_node)
                log_msg += 'ngram indexed in corpus %i\n' % corpus_id

            return JsonHttpResponse({
                'msg': log_msg,
                'text': original_text,
                'term': ngram_str,
                'id' : ngram_id,
                'group' : mainform_id,
                'count': n_added if do_indexation else 'no corpus provided for indexation'
                }, 200)

        # just in case
        except Exception as e:
            return JsonHttpResponse({
                'msg': str(e),
                'text': original_text
                }, 400)
