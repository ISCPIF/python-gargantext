#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# ****  ISIDORE  Scrapper  ***
# ****************************
# CNRS COPYRIGHTS
# SEE LEGAL LICENCE OF GARGANTEXT.ORG

from ._Crawler import *
import json
from gargantext.constants  import UPLOAD_DIRECTORY
from math                  import trunc
from gargantext.util.files import save
from gargantext.util.crawlers.sparql.bool2sparql import bool2sparql, isidore


class IsidoreCrawler(Crawler):
    ''' ISIDORE SPARQL API CLIENT'''
    
    def __init__(self):
        # Main EndPoints
        self.BASE_URL = "https://www.rechercheisidore.fr"
        self.API_URL  = "sparql"
        
        # Final EndPoints
        # TODO : Change endpoint according type of database
        self.URL   = self.BASE_URL + "/" + self.API_URL
        self.status = []

    def __format_query__(self, query=None, count=False, offset=None, limit=None):
        '''formating the query'''

        return (bool2sparql(query, count=count, offset=offset, limit=limit))


    def _get(self, query, offset=0, limit=100, lang=None):
        '''Parameters to download data'''
        
        isidore(query, count=False, offset=offset, limit=limit)

    def scan_results(self, query):
        '''
        scan_results : Returns the number of results
        Query String -> Int
        '''
        self.results_nb = [n for n in isidore(query, count=True)][0]
        return self.results_nb

    def download(self, query):
        
        downloaded = False
        
        self.status.append("fetching results")

        corpus = []
        limit = 100
        self.query_max = self.scan_results(query)
        #print("self.query_max : %s" % self.query_max)

        if self.query_max > QUERY_SIZE_N_MAX:
            msg = "Invalid sample size N = %i (max = %i)" % ( self.query_max
                                                            , QUERY_SIZE_N_MAX
                                                            )
            print("WARNING (scrap: ISIDORE d/l ): " , msg)
            self.query_max = QUERY_SIZE_N_MAX
        
        #for page in range(1, trunc(self.query_max / 100) + 2):
        for offset in range(0, self.query_max, limit):
            print("Downloading result %s to %s" % (offset, self.query_max))

            #for doc in self._get(query, count=False, offset=offset, limit=limit) :
            for doc in isidore(query, offset=offset, limit=limit) :
                corpus.append(doc)

        self.path = save( json.dumps(corpus).encode("utf-8")
                        , name='ISIDORE.json'
                        , basedir=UPLOAD_DIRECTORY
                        )
        downloaded = True
        
        return downloaded
