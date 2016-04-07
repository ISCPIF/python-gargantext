
from scrapers.MedlineFetcher import MedlineFetcher


# from datetime import datetime
from time import sleep
import json
import datetime
from os import path
import threading
#from gargantext.settings import MEDIA_ROOT, BASE_DIR

from django.shortcuts import redirect
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden

from gargantext.constants       import RESOURCETYPES
from gargantext.models.nodes    import Node
from gargantext.util.db         import session
from gargantext.util.http       import JsonHttpResponse
from gargantext.util.tools      import ensure_dir
from gargantext.util.scheduling import scheduled
from gargantext.util.toolchain  import parse_extract_indexhyperdata



# pour lire la section [scrapers] de gargantext.ini
#from configparser import ConfigParser

# --------------------------------------------------------------------
# importing constants from config file
#CONF = ConfigParser()
#with open(path.join(BASE_DIR, 'gargantext.ini')) as inifile:
#    CONF.read_file(inifile)

QUERY_SIZE_N_MAX = 1000 # int(CONF['scrappers']['QUERY_SIZE_N_MAX'])

# QUERY_SIZE_N_DEFAULT   = int(CONF['scrappers']['QUERY_SIZE_N_DEFAULT'])
# --------------------------------------------------------------------
def getGlobalStats( request ):
    """
    Pubmed year by year results

    # alist = [
    # {'string': '2011[dp] serendipity', 'queryKey': '1',
    #  'webEnv': 'NCID_1_11...._F_1', 'count': 475, 'retmax': 6},
    # {'string': '2012[dp] serendipity', 'queryKey': '1',
    #  'webEnv': 'NCID_1_14..._F_1', 'count': 345, 'retmax': 4},
    #  ... ]

    (reused as thequeries in doTheQuery)
    """
    print(request.method)
    alist = []

    if request.method == "POST":
        query = request.POST["query"]
        N = int(request.POST["N"])

        if N > QUERY_SIZE_N_MAX:
            msg = "Invalid sample size N = %i (max = %i)" % (N, QUERY_SIZE_N_MAX)
            print("ERROR(scrap: pubmed stats): ",msg)
            raise ValueError(msg)

        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" query =", query )
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" N =", N )
        instancia = MedlineFetcher()

        # serialFetcher (n_last_years, query, query_size)
        alist = instancia.serialFetcher( 5, query , N )

    data = alist
    return JsonHttpResponse(data)



def doTheQuery( request , project_id ) :
    # implicit global session
    # do we have a valid project id?
    try:
        project_id = int(project_id)
    except ValueError:
        raise Http404()
    # do we have a valid project?
    project = (session.query( Node )
                      .filter(Node.id == project_id)
                      .filter(Node.typename == 'PROJECT')
              ).first()

    if project is None:
        raise Http404()

    # do we have a valid user?
    user = request.user
    if not user.is_authenticated():
        return redirect('/auth/?next=%s' % request.path)
    if project.user_id != user.id:
        return HttpResponseForbidden()


    if request.method == "POST":
        queries = request.POST["query"]
        name    = request.POST["string"]

        # here we just realize queries already prepared by getGlobalStats
        #    ===> no need to repeat N parameter like in testISTEX <===

        instancia = MedlineFetcher()
        thequeries = json.loads(queries)

        # fyi the sum of our prepared yearly proportional quotas
        sampled_sum = sum([year_q['retmax'] for year_q in thequeries])
        print("Scrapping Pubmed: '%s' (N=%i)" % (name,sampled_sum))

        urlreqs = []
        for yearquery in thequeries:
            urlreqs.append( instancia.medlineEfetchRAW( yearquery ) )
        alist = ["tudo fixe" , "tudo bem"]


        # corpus node instanciation as a Django model
        corpus = Node(
            name = name,
            user_id = request.user.id,
            parent_id = project_id,
            typename = 'CORPUS',
                        hyperdata    = { "action"        : "Scraping data"
                                        , "language_id" : None
                                        }
        )
        session.add(corpus)
        session.commit()
        corpus_id = corpus.id
        # """
        # urlreqs: List of urls to query.
        # - Then, to each url in urlreqs you do:
        #     eFetchResult = urlopen(url)
        #     eFetchResult.read()  # this will output the XML... normally you write this to a XML-file.
        # """


        ensure_dir(request.user)
        tasks = MedlineFetcher()

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
                corpus.add_resource( type = 3
                                   , path = filename
                                   )
                dwnldsOK+=1

        if dwnldsOK == 0 :
            return JsonHttpResponse(["fail"])

        try:
            scheduled(parse_extract_indexhyperdata(corpus_id,))
        except Exception as error:
            print('WORKFLOW ERROR')
            print(error)
        sleep(1)
        return HttpResponseRedirect('/projects/' + str(project_id))

    data = alist
    return JsonHttpResponse(data)



