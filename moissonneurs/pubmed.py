# ****************************
# *****  Medline Scraper *****
# ****************************

# MEDLINE USER REQUIREMENT : Run retrieval scripts on weekends or
# between 9 pm and 5 am Eastern Time weekdays


# from datetime import datetime
from time import sleep
import json
import datetime
from os import path
import threading
from traceback                  import print_tb
#from gargantext.settings import MEDIA_ROOT, BASE_DIR

from django.shortcuts import redirect
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden

from gargantext.constants       import get_resource_by_name, QUERY_SIZE_N_MAX
from gargantext.models.nodes    import Node
from gargantext.util.db         import session
from gargantext.util.db_cache   import cache
from gargantext.util.http       import JsonHttpResponse
from gargantext.util.scheduling import scheduled
from gargantext.util.toolchain  import parse_extract_indexhyperdata

from moissonneurs.util              import Scraper



def query( request ):
    """
    Pubmed year by year results

    # alist = [
    # {'string': '2011[dp] serendipity', 'queryKey': '1',
    #  'webEnv': 'NCID_1_11...._F_1', 'count': 475, 'retmax': 6},
    # {'string': '2012[dp] serendipity', 'queryKey': '1',
    #  'webEnv': 'NCID_1_14..._F_1', 'count': 345, 'retmax': 4},
    #  ... ]

    (reused as thequeries in query_save)
    """
    print(request.method)
    alist = []

    if request.method == "POST":
        query = request.POST["query"]
        if request.POST["N"] == "NaN":
            N = QUERY_SIZE_N_MAX
        else:
            N = int(request.POST["N"])

        if N > QUERY_SIZE_N_MAX:
            msg = "Invalid sample size N = %i (max = %i)" % (N, QUERY_SIZE_N_MAX)
            print("ERROR(scrap: pubmed stats): ",msg)
            raise ValueError(msg)

        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" query =", query )
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" N =", N )
        instancia = Scraper()

        # serialFetcher (n_last_years, query, query_size)
        alist = instancia.serialFetcher( 5, query , N )

    data = alist
    return JsonHttpResponse(data)


def save( request , project_id ) :
    # implicit global session
    # do we have a valid project id?
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


    if request.method == "POST":
        queries = request.POST["query"]
        name    = request.POST["string"]

        # here we just realize queries already prepared by getGlobalStats
        #    ===> no need to repeat N parameter like in testISTEX <===

        instancia  = Scraper()
        thequeries = json.loads(queries)

        # fyi the sum of our prepared yearly proportional quotas
        sampled_sum = sum([year_q['retmax'] for year_q in thequeries])
        print("Scrapping Pubmed: '%s' (N=%i)" % (name,sampled_sum))

        urlreqs = []
        for yearquery in thequeries:
            urlreqs.append( instancia.medlineEfetchRAW( yearquery ) )
        alist = ["tudo fixe" , "tudo bem"]


        # corpus node instanciation as a Django model
        corpus = project.add_child( name=name
                                  , typename = "CORPUS"
                                  )

        # """
        # urlreqs: List of urls to query.
        # - Then, to each url in urlreqs you do:
        #     eFetchResult = urlopen(url)
        #     eFetchResult.read()  # this will output the XML... normally you write this to a XML-file.
        # """

        tasks = Scraper()

        for i in range(8):
            t = threading.Thread(target=tasks.worker2) #thing to do
            t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
            t.start()
        for url in urlreqs:
            tasks.q.put( url ) #put a task in the queue
        tasks.q.join() # wait until everything is finished

        dwnldsOK = 0

        for filename in tasks.firstResults :
            print(filename)
            if filename != False:
                # add the uploaded resource to the corpus
                corpus.add_resource( type = get_resource_by_name('Pubmed [XML]')["type"]
                                   , path = filename
                                   , url  = None
                                   )
                print("Adding the resource")
                dwnldsOK+=1

        session.add(corpus)
        session.commit()
        corpus_id = corpus.id

        if dwnldsOK == 0 :
            return JsonHttpResponse(["fail"])
        try:
            scheduled(parse_extract_indexhyperdata)(corpus_id)
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
        sleep(1)
        return HttpResponseRedirect('/projects/' + str(project_id))

    data = alist
    return JsonHttpResponse(data)
