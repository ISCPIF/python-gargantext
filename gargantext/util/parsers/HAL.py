#!/usr/bin/env python
# -*- coding: utf-8 -*-
# ****************************
# ****  HAL Parser    ***
# ****************************
# CNRS COPYRIGHTS 2017
# SEE LEGAL LICENCE OF GARGANTEXT.ORG

from ._Parser import Parser
from datetime import datetime
import json

class HalParser(Parser):
    def _parse(self, json_docs):

        hyperdata_list = []

        hyperdata_path = { "id"              : "docid"
                         , "title"           : ["en_title_s", "title_s"]
                         , "abstract"        : ["en_abstract_s", "abstract_s"]
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
                         , "docType_s"       : "docType_s"
                         }

        uris = set()

        for doc in json_docs:

            hyperdata = {}

            for key, path in hyperdata_path.items():

                # A path can be a field name or a sequence of field names
                if isinstance(path, (list, tuple)):
                    # Get first non-empty value of fields in path sequence, or None
                    field = next((x for x in (doc.get(p) for p in path) if x), None)
                else:
                    # Get field value
                    field = doc.get(path)

                if field is None:
                    field = "NOT FOUND"

                if isinstance(field, list):
                    hyperdata[key] = ", ".join(map(str, field))
                else:
                    hyperdata[key] = str(field)

            if hyperdata["url"] in uris:
                print("Document already parsed")

            else:
                uris.add(hyperdata["url"])

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

    def parse(self, filebuf):
        '''
        parse :: FileBuff -> [Hyperdata]
        '''
        contents = filebuf.read().decode("UTF-8")
        data = json.loads(contents)

        return self._parse(data)

