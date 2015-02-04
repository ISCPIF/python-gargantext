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
        metadata_list = []
        metadata_path = {
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
        metadata = {}
        import pprint
        import datetime
        for json_doc in json_docs:
            for key, path in metadata_path.items():
                try:
                    # print(path," ==> ",len(json_doc[path]))
                    metadata[key] = json_doc[path]
                except: pass

            # print("|",metadata["publication_date"])

            if "doi" in metadata: metadata["doi"] = metadata["doi"][0]
            
            keywords = []
            if "keywords" in metadata:
                for keyw in metadata["keywords"]:
                    keywords.append(keyw["value"] )
                metadata["keywords"] = ", ".join( keywords )

            moredate=False
            moresource=False
            if "host" in metadata:

                if "genre" in metadata["host"] and len(metadata["host"]["genre"])>0:
                    if "genre" in metadata and len(metadata["genre"])==0:
                        metadata["genre"] = metadata["host"]["genre"]

                # print(metadata["host"])
                if "pubdate" in metadata["host"]:
                    onebuffer = metadata["publication_date"]
                    metadata["publication_date"] = []
                    metadata["publication_date"].append(onebuffer)
                    metadata["publication_date"].append( metadata["host"]["pubdate"] )

                if "title" in metadata["host"]:
                    metadata["journal"] = metadata["host"]["title"]

            authors=False
            if "authorsRAW" in metadata:
                names = []
                for author in metadata["authorsRAW"]: 
                    names.append(author["name"])
                metadata["authors"] = ", ".join(names)

            if "host" in metadata: metadata.pop("host")
            if "genre" in metadata:
                if len(metadata["genre"])==0:
                    metadata.pop("genre")
            
            if "publication_date" in metadata and isinstance(metadata["publication_date"], list):
                if len(metadata["publication_date"])>1:
                    d1 = metadata["publication_date"][0]
                    d2 = metadata["publication_date"][1]
                    # print("date1:",d1)
                    # print("date2:",d2)
                    if len(d1)==len(d2):
                        metadata["publication_date"] = d2
                        # if int(d1)>int(d2): metadata["publication_date"] = d2
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
                        metadata["publication_date"] = fulldate
                else:
                    if "copyrightdate" in json_doc: 
                        metadata["publication_date"] = json_doc["copyrightdate"]
            else:
                if "copyrightdate" in json_doc:
                    metadata["publication_date"] = json_doc["copyrightdate"]
            
            print("||",metadata["title"])
            metadata_list.append(metadata)
            print("=============================")

        print("\nlen list:",len(metadata_list))
        return metadata_list
