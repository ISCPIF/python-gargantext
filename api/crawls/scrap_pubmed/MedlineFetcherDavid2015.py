# ****************************
# *****  Medline Fetcher *****
# ****************************

# MEDLINE USER REQUIREMENT : Run retrieval scripts on weekends or between 9 pm and 5 am Eastern Time weekdays
import sys
if sys.version_info >= (3, 0): from urllib.request import urlopen
else: from urllib import urlopen
import os
import time
# import libxml2
from lxml import etree
import datetime
from django.core.files import File
import codecs

import threading
from queue import Queue
# import time

class MedlineFetcher:

    def __init__(self):
        self.queue_size = 8
        self.q = Queue()
        self.firstResults = []
        self.lock = threading.Lock() # lock to serialize console output
        self.pubMedEutilsURL = 'http://www.ncbi.nlm.nih.gov/entrez/eutils'
        self.pubMedDB = 'Pubmed'
        self.reportType = 'medline'


    # Return the globalResults!:
    # - count = 
    # - queryKey = 
    # - webEnv = 
    def medlineEsearch(self , query):

        # print ("MedlineFetcher::medlineEsearch :")

        "Get number of results for query 'query' in variable 'count'"
        "Get also 'queryKey' and 'webEnv', which are used by function 'medlineEfetch'"
        print(query)
        origQuery = query
        query = query.replace(' ', '%20')
            
        eSearch = '%s/esearch.fcgi?db=%s&retmax=1&usehistory=y&term=%s' %(self.pubMedEutilsURL, self.pubMedDB, query)
        eSearchResult = urlopen(eSearch)
        data = eSearchResult.read()

        root = etree.XML(data)

        findcount = etree.XPath("/eSearchResult/Count/text()")
        count = findcount(root)[0]
        
        findquerykey = etree.XPath("/eSearchResult/QueryKey/text()")
        queryKey = findquerykey(root)[0]

        findwebenv = etree.XPath("/eSearchResult/WebEnv/text()")
        webEnv = findwebenv(root)[0]

        values = { "query":origQuery , "count": int(str(count)), "queryKey": queryKey , "webEnv":webEnv }
        return values


    # RETMAX:
    # Total number of UIDs from the retrieved set to be shown in the XML output (default=20)
    # maximum of 100,000 records
    def medlineEfetchRAW( self , fullquery):
        

        query = fullquery["string"]
        retmax = fullquery["retmax"]
        count = fullquery["count"]
        queryKey = fullquery["queryKey"]
        webEnv = fullquery["webEnv"]

        "Fetch medline result for query 'query', saving results to file every 'retmax' articles"

        queryNoSpace = query.replace(' ', '') # No space in directory and file names, avoids stupid errors
        
        print ("LOG::TIME: ",'medlineEfetchRAW :Query "' , query , '"\t:\t' , count , ' results')

        retstart = 0
        eFetch = '%s/efetch.fcgi?email=youremail@example.org&rettype=%s&retmode=xml&retstart=%s&retmax=%s&db=%s&query_key=%s&WebEnv=%s' %(self.pubMedEutilsURL, self.reportType, retstart, retmax, self.pubMedDB, queryKey, webEnv)
        return eFetch

    def ensure_dir(self , f):
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)

    # generic!
    def downloadFile(self, item):
        url = item[0]
        filename = item[1]
        print("\tin test_downloadFile:")
        # print(url,filename)
        data = urlopen(url)
        f = codecs.open(filename, "w" ,encoding='utf-8')
        myfile = File(f)
        myfile.write( data.read().decode('utf-8') )
        myfile.close()
        f.close()
        with self.lock:
            print(threading.current_thread().name, filename+" OK")
            return filename

    # generic!
    def test_downloadFile(self, item):
        url = item[0]
        filename = item[1]
        print("\tin downloadFile:")
        data = urlopen(url)
        return data

    # generic!
    def do_work(self,item):
        # time.sleep(1) # pretend to do some lengthy work.
        returnvalue = self.medlineEsearch(item)
        with self.lock:
            print(threading.current_thread().name, item)
            return returnvalue

    # The worker thread pulls an item from the queue and processes it
    def worker(self):
        while True:
            item = self.q.get()
            self.firstResults.append(self.do_work(item))
            self.q.task_done()

    def worker2(self):
        while True:
            item = self.q.get()
            results = []
            try: result = self.downloadFile(item)
            except: result = False
            self.firstResults.append(result)
            self.q.task_done()

    def chunks(self , l , n):
        print("chunks:")
        for i in range(0, len(l), n):
            yield l[i:i+n]

    # GLOBALLIMIT:
    # I will retrieve this exact amount of publications.
    # The publications per year i'll retrieve per year will be = (k/N)*GlobalLimit <- i'll use this as RETMAX
    # - k : Number of publications of x year (according to pubmed)
    # - N : Sum of every k belonging to {X} (total number of pubs according to pubmed)
    # - GlobalLimit : Number of publications i want.
    def serialFetcher(self , yearsNumber , query, globalLimit):

        # Create the queue and thread pool.
        for i in range(self.queue_size):
             t = threading.Thread(target=self.worker)
             t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
             t.start()
        start = time.perf_counter()

        N = 0

        print ("MedlineFetcher::serialFetcher :")
        thequeries = []
        globalresults = []
        for i in range(yearsNumber):
            year = str(2015 - i)
            print ('YEAR ' + year)
            print ('---------\n')
            pubmedquery = str(year) + '[dp] '+query
            self.q.put( pubmedquery ) #put task in the queue
        
        self.q.join()
        print('time:',time.perf_counter() - start)

        for globalresults in self.firstResults:
            # globalresults = self.medlineEsearch(pubmedquery)
            if globalresults["count"]>0:
                N+=globalresults["count"]
                querymetadata = { 
                    "string": globalresults["query"] , 
                    "count": globalresults["count"] , 
                    "queryKey":globalresults["queryKey"] , 
                    "webEnv":globalresults["webEnv"] , 
                    "retmax":0 
                }
                thequeries.append ( querymetadata )

        print("Total Number:", N,"publications")
        print("And i want just:",globalLimit,"publications")
        print("---------------------------------------\n")

        for i,query in enumerate(thequeries):
            k = query["count"]
            proportion = k/float(N)
            retmax_forthisyear = int(round(globalLimit*proportion))
            query["retmax"] = retmax_forthisyear
            if query["retmax"]==0: query["retmax"]+=1

        return thequeries
