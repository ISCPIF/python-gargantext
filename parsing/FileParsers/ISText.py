from django.db import transaction
from lxml import etree
from .FileParser import FileParser
from ..NgramsExtractors import *
from datetime import datetime
from io import BytesIO
import json

class ISText(FileParser):
    
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
            # "language_iso3"     : 'MedlineCitation/Article/Language',
            "doi"               : 'doi',
            "host"              : 'host',
            "publication_date"  : 'pubdate',
            # "authors"           : 'author',
            "authorsRAW"        : 'author',
            "keywords"          : "keywords"
        }
        hyperdata = {}
        import pprint
        import datetime
        for json_doc in json_docs:
            for key, path in hyperdata_path.items():
                try:
                    # print(path," ==> ",len(json_doc[path]))
                    hyperdata[key] = json_doc[path]
                except: pass

            # print("|",hyperdata["publication_date"])

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
            
            if "publication_date" in hyperdata and isinstance(hyperdata["publication_date"], list):
                if len(hyperdata["publication_date"])>1:
                    d1 = hyperdata["publication_date"][0]
                    d2 = hyperdata["publication_date"][1]
                    # print("date1:",d1)
                    # print("date2:",d2)
                    if len(d1)==len(d2):
                        hyperdata["publication_date"] = d2
                        # if int(d1)>int(d2): hyperdata["publication_date"] = d2
                    else:
                        fulldate = ""
                        year = d2[:4]
                        fulldate+=year
                        if len(d2)>4:
                            month = d2[4:6]
                            fulldate+="-"+month
                            if len(d2)>6:
                                day = d2[6:8]
                                fulldate+="-"+day
                        hyperdata["publication_date"] = fulldate
                else:
                    if "copyrightdate" in json_doc: 
                        hyperdata["publication_date"] = json_doc["copyrightdate"]
            else:
                if "copyrightdate" in json_doc:
                    hyperdata["publication_date"] = json_doc["copyrightdate"]
            
            print("||",hyperdata["title"])
            hyperdata_list.append(hyperdata)
            print("=============================")

        print("\nlen list:",len(hyperdata_list))
        return hyperdata_list
