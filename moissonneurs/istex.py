from datetime import datetime
from time import sleep
import datetime
import threading
from traceback                  import print_tb
#from gargantext.settings import MEDIA_ROOT, BASE_DIR

from django.shortcuts import redirect, render
from django.http import Http404, HttpResponseRedirect, HttpResponseForbidden

from gargantext.constants       import get_resource, QUERY_SIZE_N_MAX
from gargantext.models.nodes    import Node
from gargantext.util.db         import session
from gargantext.util.http       import JsonHttpResponse
from gargantext.util.scheduling import scheduled
from gargantext.util.toolchain  import parse_extract_indexhyperdata

from moissonneurs.util              import Scraper
RESOURCE_TYPE_ISTEX = 8


def query( request ):
    """
    ISTEX simply the total of hits for a query

    (not reused in testISTEX)
    """
    print(request.method)
    alist = ["bar","foo"]

    if request.method == "POST":
        query = request.POST["query"]
        if request.POST["N"] == "NaN":
            N = QUERY_SIZE_N_MAX
        else:
            N = int(request.POST["N"])
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" query =", query )
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" N =", N )
        query_string = query.replace(" ","+")
        url = "http://api.istex.fr/document/?q="+query_string+"&output=id,title,abstract,pubdate,corpusName,authors,language"

        tasks = Scraper()

        try:
            thedata_path = tasks.download( url )
            thedata = open(thedata_path, "rb")
            alist = thedata.read().decode('utf-8')
        except Exception as error:
            alist = [str(error)]
    data = alist
    return JsonHttpResponse(data)



def save(request , project_id):
    print("testISTEX:")
    print(request.method)
    alist = ["bar","foo"]
    # implicit global session
    # do we have a valid project id?
    try:
        project_id = int(project_id)
    except ValueError:
        raise Http404()

    # do we have a valid project?
    project = (session
        .query(Node)
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

    query_string = ""
    if request.method == "POST":
        query = "-"
        query_string = "-"

        #N = QUERY_SIZE_N_MAX

        if "query" in request.POST:
            query = request.POST["query"]
            query_string = query.replace(" ","+")   # url encoded q

        if "N" in request.POST:
            if request.POST["N"] == "NaN":
                N = QUERY_SIZE_N_MAX
            else:
                N = int(request.POST["N"])     # query_size from views_opti

            if N > QUERY_SIZE_N_MAX:
                N = QUERY_SIZE_N_MAX
                #msg = "Invalid sample size N = %i (max = %i)" % (N, QUERY_SIZE_N_MAX)
                #print("ERROR (scrap: istex d/l ): ",msg)
                #raise ValueError(msg)

        print("Scrapping Istex: '%s' (%i)" % (query_string , N))

        urlreqs = []
        pagesize = 50
        tasks = Scraper()
        chunks = list(tasks.chunks(range(N), pagesize))

        for k in chunks:
            if (k[0]+pagesize)>N: pagesize = N-k[0]
            urlreqs.append("http://api.istex.fr/document/?q="+query_string+"&output=id,corpusName,title,genre,language,doi,host,publicationDate,abstract,author&"+"from="+str(k[0])+"&size="+str(pagesize))

        # corpus node instanciation as a Django model

        corpus = Node(
            name = query,
            user_id = request.user.id,
            parent_id = project_id,
            typename = 'CORPUS',
                        hyperdata    = { "action"        : "Scrapping data"
                                        , "language_id" : None
                                        }
        )



        tasks = Scraper()

        for i in range(8):
            t = threading.Thread(target=tasks.worker2) #thing to do
            t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
            t.start()

        for url in urlreqs:
            tasks.q.put( url ) #put a task in th queue
        tasks.q.join() # wait until everything is finished

        dwnldsOK = 0
        for filename in tasks.firstResults:
            if filename!=False:
                # add the uploaded resource to the corpus
                corpus.add_resource(
                  type = get_resource(RESOURCE_TYPE_ISTEX)["type"]
                , path = filename
                                   )
                dwnldsOK+=1

        session.add(corpus)
        session.commit()
        #corpus_id = corpus.id

        if dwnldsOK == 0 :
            return JsonHttpResponse(["fail"])
        ###########################
        ###########################
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
