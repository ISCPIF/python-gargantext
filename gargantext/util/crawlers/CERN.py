#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# *****  CERN Scrapper    *****
# ****************************
# Author:c24b
# Date: 27/05/2015

from ._Crawler import Crawler

import hmac, hashlib
import requests
import os
import random
import urllib.parse as uparse
from lxml import etree
from gargantext.settings import API_TOKENS

#from gargantext.util.files import build_corpus_path
from gargantext.util.db import session
from gargantext.models          import Node

class CernCrawler(Crawler):
    '''CERN SCOAP3 API Interaction'''

    def __generate_signature__(self, url):
        '''creation de la signature'''
        #hmac-sha1 salted with secret
        return hmac.new(self.secret,url, hashlib.sha1).hexdigest()

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
        #add the apikey
        dict_q["apikey"] = [self.apikey]
        params = "&".join([(str(k)+"="+str(uparse.quote(v[0]))) for k,v in sorted(dict_q.items())])
        return self.BASE_URL+params

    def sign_url(self, dict_q):
        '''add signature'''
        API = API_TOKENS["CERN"]
        self.apikey = API["APIKEY"]
        self.secret  = API["APISECRET"].encode("utf-8")
        self.BASE_URL = u"http://api.scoap3.org/search?"
        url = self.__format_url__(dict_q)
        return url+"&signature="+self.__generate_signature__(url.encode("utf-8"))


    def create_corpus(self):
        #create a corpus
        corpus = Node(
            name = self.query,
            #user_id = self.user_id,
            parent_id = self.project_id,
            typename = 'CORPUS',
                        hyperdata    = { "action"        : "Scrapping data"
                                        , "language_id" : self.type["default_language"]
                                        }
        )
        #add the resource
        corpus.add_resource(
          type = self.type["type"],
          name = self.type["name"],
          path = self.path)

        try:
            print("PARSING")
            # p = eval(self.type["parser"])()
            session.add(corpus)
            session.commit()
            self.corpus_id = corpus.id
            parse_extract_indexhyperdata(corpus.id)
            return self
        except Exception as error:
            print('WORKFLOW ERROR')
            print(error)
            session.rollback()
            return self

    def download(self):
        import time
        self.path = "/tmp/results.xml"
        query = self.__format_query__(self.query)
        url = self.sign_url(query)
        start = time.time()
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
            end = time.time()
            #print (">>>>>>>>>>LOAD results", end-start)
        return downloaded


    def scan_results(self):
        '''scanner le nombre de resultat en récupérant 1 seul résultat
        qui affiche uniquement l'auteur de la page 1
        on récupère le commentaire en haut de la page
        '''
        import time


        self.results_nb = 0
        query = self.__format_query__(self.query, of="hb")
        query["ot"] = "100"
        query["jrec"]='1'
        query["rg"]='1'
        url = self.sign_url(query)
        print(url)
        #start = time.time()
        r = requests.get(url)
        #end = time.time()
        #print (">>>>>>>>>>LOAD results_nb", end-start)
        if r.status_code == 200:
            self.results_nb = int(r.text.split("-->")[0].split(': ')[-1][:-1])
            return self.results_nb
        else:
            raise ValueError(r.status)
