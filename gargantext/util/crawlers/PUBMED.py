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
from ._Crawler import Crawler
import requests
from lxml import etree

class PubmedCrawler(Crawler):
    #self.pubMedEutilsURL =
    #self.pubMedDB        = 'Pubmed'
    #self.reportType      = 'medline'

    def __format_query__(self, query= None):
        if query is not None:
        #origQuery = self.query
            query     = query.replace(' ', '%20')
            return query
        else:
            self.query     = self.query.replace(' ', '%20')
            return self.query

    def get_records_by_year(self):
        '''
        Calculate the offset results <retmax> for each year by:
        - getting the last_n_years results by year
        - respecting the proportion on the global results by year
        - sample it on the MAX_RESULTS basis
        as the following:
        pub_nb = sum([pub_nb_by_years])
        retmax = (pub_nb_year /sum([pub_nb_by_years]))*MAX_RESULTS
        '''
        _url = "http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        stats = {}

        for i in range(self.n_last_years):
            maxyear = self.YEAR -i
            minyear = maxyear-1
            #mindate = str(maxyear-1)+"/"+str(self.MONTH)
            #maxdate = str(maxyear)+"/"+str(self.MONTH)
            #print(mindate,"-",maxdate)
            params = {  "db":"pubmed",
                        "term":self.query,
                        "datetype":"pdat",
                        "retmax":1,
                        "usehistory":'y',
                        'mindate':minyear,
                        'maxdate':maxyear,
                        }
            r = requests.get(_url, params)
            if r.status_code == 200:
                data          = (r.text).encode("utf-8")
                root          = etree.XML(data)
                findcount     = etree.XPath("/eSearchResult/Count/text()")
                count         = int(findcount(root)[0])
                stats[minyear]   = count
        return stats




    def sampling(self):
        stats = self.get_records_by_year()
        _url = 'http://www.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'
        self.results_nb = sum(list(stats.values()))
        if self.results_nb == 0:
            self.status.insert(0, "[SAMPLING error] no  results found by year")
            downloaded = False
            return False

        self.paths= []
        for minyear, count in stats.items():
            print(minyear, minyear+1)
            path = "/tmp/"+str(minyear-1)+"_results.xml"
            maxyear = minyear+1
             #mindate = str(maxyear-1)+"/"+self.MONTH
            #maxdate = str(maxyear)+"/"+self.MONTH
            ratio = (count/self.results_nb)*self.MAX_RESULTS
            params = {  "email": 'youremail@example.org',
                        'rettype': 'abstract',
                        "retstart":0,
                        'retmax':round(ratio),
                        "db":"pubmed",
                        "term": self.query,
                        #"query_key": self.queryKey,
                        #"WebEnv": self.webEnv,
                        "rettype":"abstract",
                        "datetype":"pdat",
                        "mindate": str(minyear),
                        "maxdate": str(maxyear),
                        "usehistory": 'n',
                        }
            r = requests.get(_url, params, stream=True)
            with open(path, 'wb') as f:
                print(path)
                if r.status_code == 200:
                    for chunk in r.iter_content(chunk_size=1024):

                        f.write(chunk)
                        downloaded = True
                    self.paths.append(path)
                else:
                    downloaded = False
                    self.status.insert(0, "error fetching PUBMED "+ str(r))
                    break
        return downloaded

    def scan_results(self):
        self.__format_query__()
        self.base_url = 'http://www.ncbi.nlm.nih.gov/entrez/eutils'
        self.base_db= 'Pubmed'
        self.base_format = 'medline'
        self.results_nb = 0
        self.webEnv = None
        self.results_nb = 0
        self.queryKey = None
        self.retMax = 1

        _url   = '%s/esearch.fcgi?db=%s&retmax=1&usehistory=y&term=%s' \
                     % ( self.base_url, self.base_db, self.query )

        r = requests.get(_url)
        print(r.url)
        if r.status_code == 200:
            data          = (r.text).encode("utf-8")
            root          = etree.XML(data)

            findcount     = etree.XPath("/eSearchResult/Count/text()")
            self.results_nb = findcount(root)[0]

            findquerykey  = etree.XPath("/eSearchResult/QueryKey/text()")
            self.queryKey      = findquerykey(root)[0]

            findwebenv    = etree.XPath("/eSearchResult/WebEnv/text()")
            self.webEnv        = findwebenv(root)[0]
            findretmax    = etree.XPath("/eSearchResult/RetMax/text()")
            self.retMax        = findwebenv(root)[0]
            return self


    def download(self):

        #print(self.results_nb, self.queryKey, self.webEnv)
        "Fetch medline result for query 'query', saving results to file every 'retmax' articles"
        paging = 100
        self.query = self.query.replace(' ', '') # No space in directory and file names, avoids stupid errors

        # print ("LOG::TIME: ",'medlineEfetchRAW :Query "' , query , '"\t:\t' , count , ' results')

        print(self.results_nb, self.queryKey, self.webEnv)

        if self.results_nb > self.MAX_RESULTS:
            #Search results nb over the past N_YEARS
            msg = "Invalid sample size N = %i (max = %i)" % (self.results_nb, self.MAX_RESULTS)
            #print("ERROR (scrap: istex d/l ): ",msg)
            stats = self.sampling()
            #print(stats)
            #self.query_max = QUERY_SIZE_N_MAX
            return True
        else:

            #retstart = 0
            #retmax = 0
            _url = 'http://www.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?'
            params = {  "email": 'youremail@example.org',
                        'rettype': 'abstract',
                        "retstart":0,
                        'retmax':self.MAX_RESULTS,
                        "db":"Pubmed",
                        "query_key": self.queryKey,
                        "WebEnv": self.webEnv,
                        "rettype":"abstract",
                        }
            r = requests.get(_url, params, stream=True)
            print(r.url)
            #print(r.text)

            with open(self.path, 'wb') as f:
                if r.status_code == 200:
                    for chunk in r.iter_content(chunk_size=1024):
                        downloaded = True
                        f.write(chunk)
                else:
                    downloaded = False
                    self.status.insert(0, "error fetching PUBMED "+ r.status)
            return downloaded


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
                corpus.add_resource( type = resourcetype('Pubmed (XML format)')
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
