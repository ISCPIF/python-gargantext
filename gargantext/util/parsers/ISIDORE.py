#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# ****  ISIDORE Parser    ***
# ****************************
# CNRS COPYRIGHTS
# SEE LEGAL LICENCE OF GARGANTEXT.ORG

from ._Parser import Parser
from datetime import datetime
import json

class IsidoreParser(Parser):

    def parse(self, filebuf):
        '''
        parse :: FileBuff -> [Hyperdata]
        '''
        contents = filebuf.read().decode("UTF-8")
        data = json.loads(contents)
        
        filebuf.close()
        
        json_docs = data
        hyperdata_list = []
        
        hyperdata_path = { "title"    : "title"
                         , "abstract" : "abstract"
                         , "authors"  : "authors"
                         , "url"      : "url"
                         , "source"   : "source"
                         }
        
        uniq_id = set()

        for doc in json_docs:

            hyperdata = {}
            
            for key, path in hyperdata_path.items():
                    hyperdata[key] = doc.get(path, "")
            
            if hyperdata["url"] not in uniq_id:
                # Removing the duplicates implicitly
                uniq_id.add(hyperdata["url"])
                
                # Source is the Journal Name 
                hyperdata["source"] = doc.get("journal", "ISIDORE Database")
                
                # Working on the date
                maybeDate = doc.get("date"  , None)

                if maybeDate is None:
                    date = datetime.now()
                else:
                    try :
                        # Model of date: 1958-01-01T00:00:00
                        date = datetime.strptime(maybeDate, '%Y-%m-%dT%H:%M:%S')
                    except :
                        print("FIX DATE ISIDORE please >%s<" % maybeDate)
                        date = datetime.now()

                hyperdata["publication_date"] = date
                hyperdata["publication_year"]  = str(date.year)
                hyperdata["publication_month"] = str(date.month)
                hyperdata["publication_day"]   = str(date.day)
                
                hyperdata_list.append(hyperdata)
        
        return hyperdata_list
