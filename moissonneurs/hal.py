#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# ***** HAL Crawler *****
# ****************************
# LICENCE: GARGANTEXT.org Licence

RESOURCE_TYPE_HAL = 11

from django.shortcuts               import redirect, render
from django.http                    import Http404, HttpResponseRedirect \
                                                  , HttpResponseForbidden

from gargantext.constants           import get_resource, load_crawler, QUERY_SIZE_N_MAX
from gargantext.models.nodes        import Node
from gargantext.util.db             import session
from gargantext.util.db_cache       import cache
from gargantext.util.http           import JsonHttpResponse
from gargantext.util.scheduling     import scheduled
from gargantext.util.toolchain      import parse_extract_indexhyperdata


def query( request):
    '''get GlobalResults()'''
    if request.method == "POST":
        query = request.POST["query"]
        source = get_resource(RESOURCE_TYPE_HAL)
        if source["crawler"] is not None:
            crawlerbot = load_crawler(source)()
            #old raw way to get results_nb
            results = crawlerbot.scan_results(query)
            #ids = crawlerbot.get_ids(query)
            print(results)
            return JsonHttpResponse({"results_nb":crawlerbot.results_nb})

def save(request, project_id):
    '''save'''
    if request.method == "POST":

        query = request.POST.get("query")
        try:
            N = int(request.POST.get("N"))
        except:
            N = 0
        print(query, N)
        #for next time
        #ids = request.POST["ids"]
        source = get_resource(RESOURCE_TYPE_HAL)
        if N == 0:
            raise Http404()
        if N > QUERY_SIZE_N_MAX:
            N = QUERY_SIZE_N_MAX

        try:
            project_id = int(project_id)
        except ValueError:
            raise Http404()
        # do we have a valid project?
        project = session.query( Node ).filter(Node.id == project_id).first()
        if project is None:
            raise Http404()
        user = cache.User[request.user.id]
        if not user.owns(project):
            return HttpResponseForbidden()
        # corpus node instanciation as a Django model

        corpus = Node(
            name = query,
            user_id = request.user.id,
            parent_id = project_id,
            typename = 'CORPUS',
                        hyperdata    = { "action"        : "Scrapping data"
                                        }
        )

        #download_file
        crawler_bot = load_crawler(source)()
        #for now no way to force downloading X records

        #the long running command
        filename = crawler_bot.download(query)
        corpus.add_resource(
           type = source["type"]
        #,  name = source["name"]
        ,  path = crawler_bot.path
                           )

        session.add(corpus)
        session.commit()
        #corpus_id = corpus.id

        try:
            scheduled(parse_extract_indexhyperdata)(corpus.id)
        except Exception as error:
            print('WORKFLOW ERROR')
            print(error)
            try:
                print_tb(error.__traceback__)
            except:
                pass
            # IMPORTANT ---------------------------------
            # sanitize session after interrupted transact
            session.rollback()
            # --------------------------------------------

        return render(
            template_name = 'pages/projects/wait.html',
            request = request,
            context = {
                'user'   : request.user,
                'project': project,
            },
        )


    data = [query_string,query,N]
    print(data)
    return JsonHttpResponse(data)

