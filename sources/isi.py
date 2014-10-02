#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
ISI parser.
__author__ : alexandre+gargantext @ delanoe.org
__licence__ : GPL version 3.0+
__DATE__ : 2014
__VERSION__ : 1.0
"""



import os, sys
#reload(sys)
import re
import locale
# import hashlib ?

from datetime import datetime, date
from dateutil import parser

#sys.path.append("../../gargantext/")
#from .corpus import Corpus
from documents.models import Document

#TODO:
# use separators in parameters

class Isi() :
    """
    Thomson ISI parser
    """
    def __init__(self) :
        """
        See Corpus class which declare what a corpus is
        """
        # Specific declarations for Europresse
        self.data       = []

    def read_param(self,file) :
        """
        The file is an init file paramters.
        The function returns a dict of parameters for the following parse function.
        """
        source = open(file,'r')
        lines = source.readlines()
        tags={}
        for line in lines:
            if line[0] != '#':
                tag = line.split('\t')
                tags[str(tag[1])] = [str(tag[0]), str(tag[2])]
        return tags

    def rules(self, parameters) :
        """
        Interpret and does the rules described in parameters.init of each field.
        """
        pass

    def parse(self, source, bdd='isi') :
        """
        The dict needed is parameters, results of read_param function.
        The file needed is the file to be parsed in raw text only.
        """
        #source = open(file, 'r')
        lines = source.readlines()
        doc = {}
        if bdd == 'isi':
            try:
                print("reading parameters ISI")
                parameters = self.read_param('sources/parameters/isi.init')
            except Exception as e: print(e)
        elif bdd == 'ris':
            try:
                print("reading parameters RIS")
                parameters = self.read_param('sources/parameters/ris.init')
            except Exception as e: print(e)

        for key in list(parameters.keys()):
            if parameters[key][0] == 'BEGIN' :
                begin = str(key)
                del parameters[begin]
            
            elif parameters[key][0] == 'END' :
                end = str(key)
                del parameters[end]
        
        for line in lines :
            line = str(line, encoding='UTF-8')
            
            if bdd == 'ris':
                line = line.replace(' - ', '')

            if doc == {} and line[:2] == begin :
                #print(line)
                doc['url'] = " "
                key             = ""
                result          = ""

            elif line[:2] in parameters.keys() :
                
                if key != "" and key != line[:2]:
                    try:
                        doc[parameters[key][0]] = result
                    except Exception as e: print(e)
                    #doc.setdefault(parameters[key][0],[]).append(result)
                
                key = line[:2]
                result = line[2:].strip()
                
            elif line[:2] == '  ' :
                try:
                    result = result + ' ' + line[2:].strip()#.split(";")
                    
                except Exception as error :
                    print(error)
            
            elif line[:2] == end :
                doc[parameters[key][0]] = result
                try:
                    try: 
                        date = doc['year'] + " " + doc['month']
                        doc['date'] = parser.parse(date)
                    except:
                        date = doc['year']
                        doc['date'] = datetime.strptime(date, '%Y')

                except Exception as e: 
                    print('88', e)
                    try:
                        print(doc['year'])
                    except Exception as e: print('58',e)
                self.data.append(doc)
                doc = {}

    def add(self, project=None, corpus=None, user=None, ids=None):
        """ Appends notices to self.corpus from self.data removing duplicates"""
        if ids is not None:
            self.object_ids = ids
        else:
            self.object_ids = set()

        for i in self.data:
            if 'uniqu_id' not in i.keys():
                #crypt = md5.new()
                #crypt.update(i['title'])
                #i['uniqu_id'] = crypt.digest()
                i['uniqu_id'] = i['title'] + i['date']

            if i['uniqu_id'] not in self.object_ids and isinstance(i['date'], datetime):
                self.object_ids.add(i['uniqu_id'])
                doc = Document()
                
                try: 
                    doc.project = project
                except Exception as e: print(e)
                
                try:
                    doc.user    = user
                except Exception as e: print(e)

                try:
                    doc.date    = i['date']
                except Exception as e: print(e)
                    
                try:
                    doc.uniqu_id= i['uniqu_id']
                except Exception as e: print(e)
                    
                try:
                    doc.title   = i['title']
                except Exception as e: print(e)

                try:
                    doc.source  = i['source']
                except Exception as e: print(e)
                    
                try:
                    doc.authors = i['authors']
                except Exception as e: print(e)
                    
                try:
                    doc.abstract    = i['abstract']
                except Exception as e: print(e)

                try:
                    doc.save()
                except Exception as e: print(e)
                
                doc.corpus.add(corpus)

        self.data = []


def demo():
    import sys
    data = Isi()
    data.add(parameters=param, file=sys.argv[1])

if __name__ == "__main__" :
    try:
        demo()
    except Exception as error :
        print(sys.exc_traceback.tb_lineno, error)
