#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# *****  CERN Scrapper    *****
# ****************************
# Author:c24b
# Date: 27/05/2016
import hmac, hashlib
import requests
import os
import random

import urllib.parse as uparse
from lxml import etree
from gargantext.settings import API_TOKENS

from ._Crawler import Crawler
from gargantext.util.timeit_damnit  import timing


class CernCrawler(Crawler):
    '''CERN SCOAP3 API Interaction'''
    def __init__(self):
        API = API_TOKENS["CERN"]
        self.apikey = API["APIKEY"].encode("utf-8")
        self.secret  = bytearray(API["APISECRET"].encode("utf-8"))
        self.BASE_URL = u"http://api.scoap3.org/search?"

    def __generate_signature__(self, url):
        '''creation de la signature'''
        #hmac-sha1 salted with secret
        return hmac.new(self.secret,url.encode("utf-8"), hashlib.sha1).hexdigest()

    def __format_query__(self, query, of="xm", fields= None):
        ''' for query filters params
        see doc https://scoap3.org/scoap3-repository/xml-api/
        '''
        #dict_q = uparse.parse_qs(query)
        dict_q = {}
        #by default: search by pattern
        dict_q["p"] = query
        if fields is not None and isinstance(fields, list):
            fields = ",".join(fields)
            dict_q["f"] = fields
        #outputformat: "xm", "xmt", "h", "html"
        dict_q["of"]= of
        return dict_q

    def __format_url__(self, dict_q):
        '''format the url with encoded query'''
        #add the apikey at the end
        dict_q["apikey"] = self.apikey
        #dict_q["p"] = dict_q["p"].replace(" ", "+") >> quote_plus
        params = ("&").join([(str(k)+"="+uparse.quote_plus(v)) for k,v in sorted(dict_q.items())])
        return self.BASE_URL+params

    def sign_url(self, dict_q):
        '''add signature'''
        url = self.__format_url__(dict_q)
        return url+"&signature="+self.__generate_signature__(url)

    @timing
    def download(self, query):
        self.path = "/tmp/results.xml"
        query = self.__format_query__(query)
        url = self.sign_url(query)
        r = requests.get(url, stream=True)
        downloaded = False
        #the long part
        with open(self.path, 'wb') as f:
            print("Downloading file")
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    #print("===")
                    f.write(chunk)
            downloaded = True
        return downloaded

    def get_ids(self, query):
        '''get results nb + individual ids of search query return every time 200 ids'''
        dict_q = uparse.parse_qs(query)
        #parameters for a global request
        dict_q["p"] = query
        dict_q["of"] = "id"
        dict_q["rg"] = "10000"
        #api key is added when formatting url
        url = self.__format_url__(dict_q)
        signed_url = url+"&signature="+self.__generate_signature__(url)
        r = requests.get(signed_url)
        print(signed_url)
        self.ids = r.json()
        print(type(self.ids), len(self.ids))
        #self.ids = (",").split(j_ids.replace("[|]", ""))

        self.results_nb = len(self.ids)
        print(self.results_nb, "res")
        #self.generate_urls()
        return(self.ids)
    
    def generate_urls(self):
        ''' generate raw urls of ONE record'''
        self.urls = ["http://repo.scoap3.org/record/%i/export/xm?ln=en" %rid for rid in self.ids]
        return self.urls
    
    def fetch_records(self, ids):
        ''' for NEXT time'''
        raise NotImplementedError

    @timing
    def scan_results(self, query):
        '''[OLD]scanner le nombre de resultat en récupérant 1 seul résultat
        qui affiche uniquement l'auteur de la page 1
        on récupère le commentaire en haut de la page
        '''
        self.results_nb = 0
        query = self.__format_query__(query, of="hb")
        query["ot"] = "100"
        query["jrec"]='1'
        query["rg"]='1'
        url = self.sign_url(query)
        #print(url)
        #start = time.time()
        r = requests.get(url)
        #end = time.time()
        #print (">>>>>>>>>>LOAD results_nb", end-start)
        if r.status_code == 200:
            self.results_nb = int(r.text.split("-->")[0].split(': ')[-1][:-1])
            return self.results_nb
        else:
            raise ValueError(r.status)
