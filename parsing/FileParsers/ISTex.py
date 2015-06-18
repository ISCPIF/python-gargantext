from django.db import transaction
from lxml import etree
from .FileParser import FileParser
from ..NgramsExtractors import *
from datetime import datetime
from io import BytesIO
import json

class ISTex(FileParser):
    
    def _parse(self, thefile):
        json_data=open(thefile,"r")
        data = json.load(json_data)
        json_data.close()
        json_docs = data["hits"]
        hyperdata_list = []
        hyperdata_path = {
            "id"                : "id",
            "source"           : 'corpusName',
            "title"             : 'title',
            "genre"             : "genre",
            "language_iso3"     : 'language',
            "doi"               : 'doi',
            "host"              : 'host',
            "publication_date"  : 'pubdate',
            # "authors"           : 'author',
            "authorsRAW"        : 'author',
            "keywords"          : "keywords"
        }
        
        for json_doc in json_docs:
            hyperdata = {}
            for key, path in hyperdata_path.items():
                try:
                    # print(path," ==> ",len(json_doc[path]))
                    hyperdata[key] = json_doc[path]
                except: pass

            # print("|",hyperdata["language_iso3"])

            if "doi" in hyperdata: hyperdata["doi"] = hyperdata["doi"][0]
            
            keywords = []
            if "keywords" in hyperdata:
                for keyw in hyperdata["keywords"]:
                    keywords.append(keyw["value"] )
                hyperdata["keywords"] = ", ".join( keywords )

            moredate=False
            moresource=False
            if "host" in hyperdata:

                if "genre" in hyperdata["host"] and len(hyperdata["host"]["genre"])>0:
                    if "genre" in hyperdata and len(hyperdata["genre"])==0:
                        hyperdata["genre"] = hyperdata["host"]["genre"]

                # print(hyperdata["host"])
                if "pubdate" in hyperdata["host"]:
                    onebuffer = hyperdata["publication_date"]
                    hyperdata["publication_date"] = []
                    hyperdata["publication_date"].append(onebuffer)
                    hyperdata["publication_date"].append( hyperdata["host"]["pubdate"] )

                if "title" in hyperdata["host"]:
                    hyperdata["journal"] = hyperdata["host"]["title"]

            authors=False
            if "authorsRAW" in hyperdata:
                names = []
                for author in hyperdata["authorsRAW"]: 
                    names.append(author["name"])
                hyperdata["authors"] = ", ".join(names)

            if "host" in hyperdata: hyperdata.pop("host")
            if "genre" in hyperdata:
                if len(hyperdata["genre"])==0:
                    hyperdata.pop("genre")
            if "language_iso3" in hyperdata:
                hyperdata["language_iso3"] = hyperdata["language_iso3"][0]

            RealDate = hyperdata["publication_date"]
            if "publication_date" in hyperdata: hyperdata.pop("publication_date")

            
            Decision=""
            if len(RealDate)>4:
                if len(RealDate)>8:
                    try: Decision = datetime.strptime(RealDate, '%Y-%b-%d').date()
                    except: 
                        try: Decision = datetime.strptime(RealDate, '%Y-%m-%d').date()
                        except: Decision=False
                else: 
                    try: Decision = datetime.strptime(RealDate, '%Y-%b').date()
                    except: 
                        try: Decision = datetime.strptime(RealDate, '%Y-%m-%d').date()
                        except: Decision=False
            else: 
                try: Decision = datetime.strptime(RealDate, '%Y-%m-%d').date()
                except: Decision=False
            
            if Decision!=False:
                hyperdata["publication_year"] = str(Decision.year)
                hyperdata["publication_month"] = str(Decision.month)
                hyperdata["publication_day"] = str(Decision.day)
                hyperdata_list.append(hyperdata)
                # print("\t||",hyperdata["title"])
                # print("\t\t",Decision)
                # print("=============================")

        return hyperdata_list
