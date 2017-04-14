#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# ****  MULTIVAC Scrapper  ***
# ****************************
# CNRS COPYRIGHTS
# SEE LEGAL LICENCE OF GARGANTEXT.ORG

from ._Crawler import *
import json

class ISTexCrawler(Crawler):
    """
    ISTEX Crawler
    """
    def __format_query__(self,query=None):
        '''formating query urlquote instead'''
        if query is not None:
            query = query.replace(" ","+")
            return query
        else:
            self.query = self.query.replace(" ","+")
            return self.query

    def scan_results(self):
        #get the number of results
        self.results_nb = 0
        self.query = self.__format_query__()
        _url = "http://api.istex.fr/document/?q="+self.query+"&size=0"
        #"&output=id,title,abstract,pubdate,corpusName,authors,language"
        r = requests.get(_url)
        print(r)
        if r.status_code == 200:
            self.results_nb = int(r.json()["total"])
            self.status.append("fetching results")
            return self.results_nb
        else:
            self.status.append("error")
            raise ValueError(r.status)

    def download(self):
        '''fetching items'''
        downloaded = False
        def get_hits(future):
            '''here we directly get the result hits'''
            response = future.result()
            if response.status_code == 200:
                return response.json()["hits"]
            else:
                return None

        #session = FuturesSession()
        #self.path = "/tmp/results.json"
        self.status.append("fetching results")
        paging = 100
        self.query_max = self.results_nb
        if self.query_max > QUERY_SIZE_N_MAX:
            msg = "Invalid sample size N = %i (max = %i)" % (self.query_max, QUERY_SIZE_N_MAX)
            print("ERROR (scrap: istex d/l ): ",msg)
            self.query_max = QUERY_SIZE_N_MAX

        #urlreqs = []
        with open(self.path, 'wb') as f:
            for i in range(0, self.query_max, paging):
                url_base = "http://api.istex.fr/document/?q="+self.query+"&output=*&from=%i&size=%i" %(i, paging)
                r = requests.get(url_base)
                if r.status_code == 200:
                    downloaded = True
                    f.write(r.text.encode("utf-8"))
                else:
                    downloaded = False
                    self.status.insert(0, "error fetching ISTEX "+ r.status)
                    break
        return downloaded




