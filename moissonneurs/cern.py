#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# *****  CERN Scrapper    *****
# ****************************

import logging

from logging.handlers import RotatingFileHandler

# création de l'objet logger qui va nous servir à écrire dans les logs
logger = logging.getLogger()
# on met le niveau du logger à DEBUG, comme ça il écrit tout
logger.setLevel(logging.DEBUG)

# création d'un formateur qui va ajouter le temps, le niveau
# de chaque message quand on écrira un message dans le log
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

# création d'un handler qui va rediriger une écriture du log vers
# un fichier en mode 'append', avec 1 backup et une taille max de 1Mo
#>>> Permission denied entre en conflit avec les los django
#file_handler = RotatingFileHandler('.activity.log', 'a', 1000000, 1)
# on lui met le niveau sur DEBUG, on lui dit qu'il doit utiliser le formateur
# créé précédement et on ajoute ce handler au logger
#~ file_handler.setLevel(logging.DEBUG)
#~ file_handler.setFormatter(formatter)
#~ logger.addHandler(file_handler)

# création d'un second handler qui va rediriger chaque écriture de log
# sur la console
steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.DEBUG)
logger.addHandler(steam_handler)

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

def save( request , project_id ) :
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
        raise HttpResponseForbidden()


    if request.method == "POST":
        query = request.POST["query"]

        name    = request.POST["string"]
        corpus = project.add_child( name=name
                                , typename = "CORPUS"
                                  )
        corpus.add_resource( type = resourcetype('Cern (MARC21 XML)')
                                   , path = filename
                                   , url  = None
                                   )
        print("Adding the resource")

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
        #Here Requests API
        #
        #API_TOKEN = API["CERN"]

        #instancia = Scraper()

        # serialFetcher (n_last_years, query, query_size)
        #alist = instancia.serialFetcher( 5, query , N )

    data = alist
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
