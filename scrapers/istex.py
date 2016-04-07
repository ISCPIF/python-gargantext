def getGlobalStatsISTEXT(request ):
    """
    ISTEX simply the total of hits for a query

    (not reused in testISTEX)
    """
    print(request.method)
    alist = ["bar","foo"]

    if request.method == "POST":
        query = request.POST["query"]
        N = int(request.POST["N"])
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" query =", query )
        print ("LOG::TIME:_ "+datetime.datetime.now().isoformat()+" N =", N )
        query_string = query.replace(" ","+")
        url = "http://api.istex.fr/document/?q="+query_string+"&output=id,title,abstract,pubdate,corpusName,authors,language"

        tasks = MedlineFetcher()

        try:
            thedata_path = tasks.download( url )
            thedata = open(thedata_path, "rb")
            alist = thedata.read().decode('utf-8')
        except Exception as error:
            alist = [str(error)]
    data = alist
    return JsonHttpResponse(data)




def testISTEX(request , project_id):
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



    if request.method == "POST":
        query = "-"
        query_string = "-"
        N = 0

        if "query" in request.POST:
            query = request.POST["query"]
            query_string = query.replace(" ","+")   # url encoded q

        if "N" in request.POST:
            N = int(request.POST["N"])     # query_size from views_opti
            if N > QUERY_SIZE_N_MAX:
                msg = "Invalid sample size N = %i (max = %i)" % (N, QUERY_SIZE_N_MAX)
                print("ERROR (scrap: istex d/l ): ",msg)
                raise ValueError(msg)

        print("Scrapping Istex: '%s' (%i)" % (query_string , N))

        urlreqs = []
        pagesize = 50
        tasks = MedlineFetcher()
        chunks = list(tasks.chunks(range(N), pagesize))
        for k in chunks:
            if (k[0]+pagesize)>N: pagesize = N-k[0]
            urlreqs.append("http://api.istex.fr/document/?q="+query_string+"&output=*&"+"from="+str(k[0])+"&size="+str(pagesize))


        resourcetype = RESOURCETYPES["name"]["ISTex"]

        # corpus node instanciation as a Django model
        corpus = Node(
            name = query,
            user_id = request.user.id,
            parent_id = project_id,
            typename = 'CORPUS',
            language_id = None,
            hyperdata    = {'Processing' : "Parsing documents",}
        )
        session.add(corpus)
        session.commit()
        corpus_id = corpus.id

        print("NEW CORPUS", corpus_id)
        ensure_dir(request.user)
        tasks = MedlineFetcher()

        for i in range(8):
            t = threading.Thread(target=tasks.worker2) #thing to do
            t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
            t.start()
        for url in urlreqs:
            filename = MEDIA_ROOT + '/corpora/%s/%s' % (request.user, str(datetime.datetime.now().isoformat()))
            tasks.q.put( [url , filename]) #put a task in th queue
        tasks.q.join() # wait until everything is finished

        dwnldsOK = 0
        for filename in tasks.firstResults:
            if filename!=False:
                # add the uploaded resource to the corpus
                corpus.add_resource(corpus,
                    user_id = request.user.id,
                    type_id = resourcetype.id,
                    file = filename,
                )
                dwnldsOK+=1
        if dwnldsOK == 0: return JsonHttpResponse(["fail"])
        ###########################
        ###########################
        try:
            scheduled(parse_extract_indexhyperdata(corpus_id,))
        except Exception as error:
            print('WORKFLOW ERROR')
            print(error)
        sleep(1)
        return HttpResponseRedirect('/project/' + str(project_id))


    data = [query_string,query,N]
    return JsonHttpResponse(data)


