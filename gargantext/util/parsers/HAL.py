#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# ****  HAL Parser    ***
# ****************************
# CNRS COPYRIGHTS
# SEE LEGAL LICENCE OF GARGANTEXT.ORG

from ._Parser import Parser
from datetime import datetime
import json

class HalParser(Parser):

    def parse(self, filebuf):
        '''
        parse :: FileBuff -> [Hyperdata]
        '''
        contents = filebuf.read().decode("UTF-8")
        data = json.loads(contents)
        
        filebuf.close()
        
        json_docs = data
        hyperdata_list = []
        
        hyperdata_path = { "id"              : "isbn_s"
                         , "title"           : "title_s"
                         , "abstract"        : "abstract_s"
                         , "source"          : "journalTitle_s"
                         , "url"             : "uri_s"
                         , "authors"         : "authFullName_s"
                         , "isbn_s"          : "isbn_s"
                         , "issue_s"         : "issue_s"
                         , "language_s"      : "language_s"
                         , "doiId_s"         : "doiId_s"
                         , "authId_i"        : "authId_i"
                         , "instStructId_i"  : "instStructId_i"
                         , "deptStructId_i"  : "deptStructId_i"
                         , "labStructId_i"   : "labStructId_i"
                         , "rteamStructId_i" : "rteamStructId_i" 
                         }

        uris = set()

        for doc in json_docs:

            hyperdata = {}
            
            for key, path in hyperdata_path.items():
                    
                    field = doc.get(path, "NOT FOUND")
                    if isinstance(field, list):
                        hyperdata[key] = ", ".join(map(lambda x: str(x), field))
                    else:
                        hyperdata[key] = str(field)
            
            if hyperdata["url"] in uris:
                print("Document already parsed")
            else:
                uris.add(hyperdata["url"])
#            hyperdata["authors"] = ", ".join(
#                                             [ p.get("person", {})
#                                                .get("name"  , "")
#                          
#                                               for p in doc.get("hasauthor", [])
#                                             ]
#                                            )
#            
                maybeDate = doc.get("submittedDate_s", None)

                if maybeDate is not None:
                    date = datetime.strptime(maybeDate, "%Y-%m-%d %H:%M:%S")
                else:
                    date = datetime.now()

                hyperdata["publication_date"] = date
                hyperdata["publication_year"]  = str(date.year)
                hyperdata["publication_month"] = str(date.month)
                hyperdata["publication_day"]   = str(date.day)
                
                hyperdata_list.append(hyperdata)
        
        return hyperdata_list
