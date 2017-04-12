#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# ****  MULTIVAC Scrapper  ***
# ****************************
# CNRS COPYRIGHTS
# SEE LEGAL LICENCE OF GARGANTEXT.ORG

from ._Crawler import *
import json
from gargantext.settings  import API_TOKENS
from gargantext.constants import UPLOAD_DIRECTORY
from math import trunc
from gargantext.util.files import save

class MultivacCrawler(Crawler):
    ''' Multivac API CLIENT'''
    
    def __init__(self):
        self.apikey = API_TOKENS["MULTIVAC"]
        
        # Main EndPoints
        self.BASE_URL = "https://api.iscpif.fr/v2"
        self.API_URL  = "pvt/economy/repec/search"
        
        # Final EndPoints
        # TODO : Change endpoint according type of database
        self.URL   = self.BASE_URL + "/" + self.API_URL
        self.status = []

    def __format_query__(self, query=None):
        '''formating the query'''
        
        if query is not None:
            self.query = query
            return self.query
        else:
            self.query = ""
            return self.query
    

    def _get(self, query, fromPage=1, count=10, lang=None):
        # Parameters
        querystring = { "q"       : query
                      , "count"   : count
                      , "from"    : fromPage
                      , "api_key" : API_TOKENS["MULTIVAC"]["APIKEY"]
                      }
        
        if lang is not None:
            querystring["lang"] = lang
        
        # Specify Headers
        headers = { "cache-control" : "no-cache" }
        
        
        # Do Request and get response
        response = requests.request( "GET"
                                   , self.URL
                                   , headers = headers
                                   , params  = querystring
                                   )
        
        print(querystring)
        # Validation : 200 if ok else raise Value
        if response.status_code == 200:
            charset = response.headers["Content-Type"].split("; ")[1].split("=")[1]
            return (json.loads(response.content.decode(charset)))
        else:
            raise ValueError(response.status_code, response.reason)
        
    def scan_results(self, query):
        '''
        scan_results : Returns the number of results
        Query String -> Int
        '''
        self.results_nb = 0
        total = self._get(query)["results"]["total"]
        self.results_nb = total

        return self.results_nb

    def download(self, query):
        
        downloaded = False
        
        self.status.append("fetching results")

        corpus = []
        paging = 100
        self.query_max = self.scan_results(query)
        
        if self.query_max > QUERY_SIZE_N_MAX:
            msg = "Invalid sample size N = %i (max = %i)" % (self.query_max, QUERY_SIZE_N_MAX)
            print("ERROR (scrap: multivac d/l ): ",msg)
            self.query_max = QUERY_SIZE_N_MAX
        
        for page in range(1, trunc(self.query_max / 100) + 1):
            docs = self._get(query, fromPage=page, count=paging)["results"]["hits"]
            for doc in docs:
                corpus.append(doc)

        self.path = save(json.dumps(corpus).encode("utf-8"), name='Multivac.json', basedir=UPLOAD_DIRECTORY )
        downloaded = True
        
        return downloaded
