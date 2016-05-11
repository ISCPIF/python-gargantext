# ****************************
# *****  CERN Scrapper    *****
# ****************************
import json
import datetime
from os import path
import threading
import hmac, hashlib
import requests
import lxml
import subprocess
import urllib.parse as uparse
from lxml import etree
from bs4 import BeautifulSoup, Comment
from collections import defaultdict



#from gargantext.util.files import download

from gargantext.settings import API_TOKENS as API
#from private import API_PERMISSIONS
API_TOKEN = API["CERN"]
def query( request ):
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

def save(request , project_id):
    print("testCERN:")
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
        tasks = Scraper()
        chunks = list(tasks.chunks(range(N), pagesize))
        for k in chunks:
            if (k[0]+pagesize)>N: pagesize = N-k[0]
            urlreqs.append("http://api.istex.fr/document/?q="+query_string+"&output=*&"+"from="+str(k[0])+"&size="+str(pagesize))

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
                  type = resourcetype('ISTex')
                , path = filename
                                   )
                dwnldsOK+=1

        session.add(corpus)
        session.commit()
        corpus_id = corpus.id

        if dwnldsOK == 0 :
            return JsonHttpResponse(["fail"])
        ###########################
        ###########################
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

        return render(
            template_name = 'pages/projects/wait.html',
            request = request,
            context = {
                'user'   : request.user,
                'project': project,
            },
        )


    data = [query_string,query,N]
    return JsonHttpResponse(data)


class CERN_API(object):
    '''CERN SCOAP3 Interaction'''
    def __init__(self,query, filename= "./results.xml"):
        self.query = query
        self.apikey = API["TOKEN"]
        self.secret  = API["SECRET"].encode("utf-8")
        self.results = self.get_results(filename)
        self.BASE_URL= u"http://api.scoap3.org/search?"
    def __generate_signature__(self, url):
        '''creation de la signature'''
        #hmac-sha1 salted with secret
        return hmac.new(self.secret,url, hashlib.sha1).hexdigest()

    def __format_url__(self):
        '''format the url with encoded query'''
        dict_q = uparse.parse_qs(self.query)
        #add the apikey
        dict_q["apikey"] = [self.apikey]
        params = "&".join([(str(k)+"="+str(uparse.quote(v[0]))) for k,v in sorted(dict_q.items())])
        return self.BASE_URL+params

    def sign_url(self):
        '''add signature'''
        url = self.__format_url__()
        return url+"&signature="+self.__generate_signature__(url.encode("utf-8"))

    def get_results(self, filename):
        url = self.sign_url()
        r = requests.get(url, stream=True)
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
        return filename
    def parse_xml(filename,MARCXML):
        parser = etree.XMLParser()
        with open(self.filename, 'r') as f:
            root = etree.tostring(f.read())
            data = f.read()
            records = []
            for record in data.split("<record>")[1:]:
                soup = BeautifulSoup("<record>"+record, "lxml")
                r = {v:[] for v in self.MARC21["700"].values()}
                r["uid"]  = soup.find("controlfield").text

                for data in soup.find_all("datafield"):
                    tag = data.get("tag")
                    if tag in self.MARC21.keys():
                        for sub in data.find_all("subfield"):
                            code = sub.get("code")
                            if code in self.MARC21[tag].keys():
                                if tag == "700":
                                    r[self.MARC21[tag][code]].append(sub.text)
                                else:
                                    r[self.MARC21[tag][code]] = sub.text
                records.append(r.decode('utf-8'))
        return JsonHttpResponse(records)


#query="of=xm"
#a = CERN_API(query, "./full.xml")
#p = CERNParser("./full.xml")
#print(p.MARC21.keys())
#~ #p.parse()
#~ with open("./results_full.json", "r") as f:
    #~ data = json.load(f)
    #~ for record in data["records"]:
        #~ print(record.keys())
