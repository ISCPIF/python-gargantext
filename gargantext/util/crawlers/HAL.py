#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# ****  HAL      Scrapper  ***
# ****************************
# CNRS COPYRIGHTS
# SEE LEGAL LICENCE OF GARGANTEXT.ORG

from ._Crawler import *
import json
from gargantext.constants  import UPLOAD_DIRECTORY
from math                  import trunc
from gargantext.util.files import save

class HalCrawler(Crawler):
    ''' HAL API CLIENT'''
    
    def __init__(self):
        # Main EndPoints
        self.BASE_URL = "https://api.archives-ouvertes.fr"
        self.API_URL  = "search"
        
        # Final EndPoints
        # TODO : Change endpoint according type of database
        self.URL   = self.BASE_URL + "/" + self.API_URL
        self.status = []

    def __format_query__(self, query=None):
        '''formating the query'''

        #search_field="title_t"
        search_field="abstract_t"

        return (search_field + ":" + "(" + query  + ")")


    def _get(self, query, fromPage=1, count=10, lang=None):
        # Parameters

        fl = """ title_s
               , abstract_s
               , submittedDate_s
               , journalDate_s
               , authFullName_s
               , uri_s
               , isbn_s
               , issue_s
               , journalPublisher_s
             """
               #, authUrl_s
               #, type_s
        
        wt = "json"

        querystring = { "q"       : query
                      , "rows"    : count
                      , "start"   : fromPage
                      , "fl"      : fl
                      , "wt"      : wt
                      }
        
        # Specify Headers
        headers = { "cache-control" : "no-cache" }
        
        
        # Do Request and get response
        response = requests.request( "GET"
                                   , self.URL
                                   , headers = headers
                                   , params  = querystring
                                   )
        
        #print(querystring)
        # Validation : 200 if ok else raise Value
        if response.status_code == 200:
            charset = ( response.headers["Content-Type"]
                                .split("; ")[1]
                                .split("=" )[1]
                      )
            return (json.loads(response.content.decode(charset)))
        else:
            raise ValueError(response.status_code, response.reason)
        
    def scan_results(self, query):
        '''
        scan_results : Returns the number of results
        Query String -> Int
        '''
        self.results_nb = 0
        
        total = ( self._get(query)
                      .get("response", {})
                      .get("numFound"  ,  0)
                )
        
        self.results_nb = total

        return self.results_nb

    def download(self, query):
        
        downloaded = False
        
        self.status.append("fetching results")

        corpus = []
        paging = 100
        self.query_max = self.scan_results(query)
        #print("self.query_max : %s" % self.query_max)

        if self.query_max > QUERY_SIZE_N_MAX:
            msg = "Invalid sample size N = %i (max = %i)" % ( self.query_max
                                                            , QUERY_SIZE_N_MAX
                                                            )
            print("ERROR (scrap: Multivac d/l ): " , msg)
            self.query_max = QUERY_SIZE_N_MAX
        
        #for page in range(1, trunc(self.query_max / 100) + 2):
        for page in range(0, self.query_max, paging):
            print("Downloading page %s to %s results" % (page, paging))
            docs = (self._get(query, fromPage=page, count=paging)
                        .get("response", {})
                        .get("docs"   , [])
                   )

            for doc in docs:
                corpus.append(doc)

        self.path = save( json.dumps(corpus).encode("utf-8")
                        , name='HAL.json'
                        , basedir=UPLOAD_DIRECTORY
                        )
        downloaded = True
        
        return downloaded
