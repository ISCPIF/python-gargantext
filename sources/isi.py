import os, sys
#reload(sys)
import re
import locale
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
        self.object_ids = []

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
                tags[tag[1]] = [tag[0], tag[2]]
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
        document = {}
        if bdd == 'isi':
            parameters = self.read_param('sources/parameters/isi.init')
        elif bdd == 'ris':
            parameters = self.read_param('sources/parameters/ris.init')


        for key in list(parameters.keys()):
            if parameters[key][0] == 'BEGIN' :
                begin = str(key)
                del parameters[begin]
            
            elif parameters[key][0] == 'END' :
                end = str(key)
                del parameters[end]
        
        for line in lines :
            if document == {} and line[:2] == begin :
                document['url'] = " "
                key             = ""
                result          = ""

            elif line[:2] in parameters.keys() :
                
                if key != "" and key != line[:2]:
                    try:
                        document[parameters[key][0]] = result
                    except Exception as e: print(e)
                    #document.setdefault(parameters[key][0],[]).append(result)
                
                key = line[:2]
                result = line[2:].strip()
                
            elif line[:2] == '  ' :
                try:
                    result = result + ' ' + line[2:].strip()#.split(";")
                    
                except Exception as error :
                    pass
            
            elif line[:2] == end :
                document[parameters[key][0]] = result
                
                try:
                    try: 
                        date = document['year'] + " " + document['month']
                        document['date'] = parser.parse(date)
                    except:
                        date = document['year']
                        document['date'] = datetime.strptime(date, '%Y')

                except Exception as e: print('88', e)
                self.data.append(document)
                document = {}

    def add(self, project=None, corpus=None, user=None):
        """ Appends notices to self.corpus from self.data removing duplicates"""
        for i in self.data:
            if i['uniqu_id'] not in self.object_ids and isinstance(i['date'], datetime):
                self.object_ids.append(i['uniqu_id'])
                doc = Document()
                
                doc.project = project
                doc.user    = user

                doc.date    = i['date']
                doc.uniqu_id= i['uniqu_id']
                doc.title   = i['title']
                print(doc.project)

                doc.source  = i['source']
                doc.authors = i['authors']
                doc.text    = i['text']

                doc.save()
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
