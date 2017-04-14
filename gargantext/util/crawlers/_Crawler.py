# Scrapers config
QUERY_SIZE_N_MAX     = 1000

from gargantext.constants import get_resource, QUERY_SIZE_N_MAX
from gargantext.util.scheduling import scheduled
from gargantext.util.db         import session
from requests_futures.sessions import FuturesSession
from gargantext.util.db         import session
import requests
from gargantext.models.nodes    import Node
#from gargantext.util.toolchain import parse_extract_indexhyperdata
from datetime import date

class Crawler:
    """Base class for performing search and add corpus file depending on the type
    """
    def __init__(self, record):

        #the name of corpus
        #that will be built in case of internal fileparsing
        self.record       = record
        self.name         = record["corpus_name"]
        self.project_id   = record["project_id"]
        self.user_id      = record["user_id"]
        self.resource     = record["source"]
        self.type         = get_resource(self.resource)
        self.query        = record["query"]
        #format the sampling
        self.n_last_years = 5
        self.YEAR         = date.today().year
        #pas glop
        # mais easy version
        self.MONTH        = str(date.today().month)
        
        if len(self.MONTH) == 1:
            self.MONTH = "0"+self.MONTH
        
        self.MAX_RESULTS = QUERY_SIZE_N_MAX
        
        try:
            self.results_nb = int(record["count"])
        except KeyError:
            #n'existe pas encore
            self.results_nb = 0
        try:
            self.webEnv   = record["webEnv"]
            self.queryKey = record["queryKey"]
            self.retMax   = record["retMax"]
        except KeyError:
            #n'exsite pas encore
            self.queryKey = None
            self.webEnv = None
            self.retMax = 1
        self.status = [None]
        self.path = "/tmp/results.txt"

    def tmp_file(self):
        '''here should stored the results
        depending on the type of format'''
        raise NotImplemented


    def parse_query(self):
        '''here should parse the parameters of the query
        depending on the type and retrieve a set of activated search option
        '''
        raise NotImplemented

    def fetch(self):
        if self.download():
            self.create_corpus()
            return self.corpus_id
    
    def get_sampling_dates():
        '''Create a sample list of min and max date based on Y and M f*
        or N_LAST_YEARS results'''
        dates = []
        for i in range(self.n_last_years):
            maxyear = self.YEAR -i
            mindate = str(maxyear-1)+"/"+str(self.MONTH)
            maxdate = str(maxyear)+"/"+str(self.MONTH)
            print(mindate,"-",maxdate)
            dates.append((mindate, maxdate))
        return dates

    def create_corpus(self):
        #create a corpus
        corpus = Node(
            name = self.query,
            user_id = self.user_id,
            parent_id = self.project_id,
            typename = 'CORPUS',
                        hyperdata    = { "action"        : "Scrapping data",
                                         "language_id" : self.type["default_language"],
                                        }
        )
        self.corpus_id = corpus.id
        if len(self.paths) > 0:
            for path in self.paths:
                #add the resource
                corpus.add_resource(
                  type = self.type["type"],
                  name = self.type["name"],
                  path = path
                  )
            session.add(corpus)
            session.commit()
            scheduled(parse_extract_indexhyperdata(corpus.id))
        else:
            #add the resource
            corpus.add_resource(
              type = self.type["type"],
              name = self.type["name"],
              path = self.path
              )
            session.add(corpus)
            session.commit()
            scheduled(parse_extract_indexhyperdata(corpus.id))
        return corpus
