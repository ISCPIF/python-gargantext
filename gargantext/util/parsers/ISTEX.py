from ._Parser import Parser
from datetime import datetime
from io import BytesIO
import json

class ISTexParser(Parser):

    def parse(self, filebuf):
        contents = filebuf.read().decode("UTF-8")
        data = json.loads(contents)
        filebuf.close()
        json_docs = data["hits"]
        hyperdata_list = []
        hyperdata_path = {
            "id"                : "id",
            "source"            : "corpusName",
            "title"             : "title",
            "genre"             : "genre",
            "language_iso3"     : "language",
            "doi"               : "doi",
            "host"              : "host",
            "publication_date"  : "publicationDate",
            "abstract"          : "abstract",
            # "authors"           : 'author',
            "authorsRAW"        : "author",
            #"keywords"          : "keywords"
        }

        suma = 0
        
        for json_doc in json_docs:

            hyperdata = {}
            for key, path in hyperdata_path.items():
                try:
                    # print(path," ==> ",len(json_doc[path]))
                    hyperdata[key] = json_doc[path]
                except:
                    pass

            # print("|",hyperdata["language_iso3"])

            if "doi" in hyperdata:
                hyperdata["doi"] = hyperdata["doi"][0]

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
                    hyperdata["source"] = hyperdata["host"]["title"]

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
                # retrieve lang if lang != [] and lang != ["unknown"]
                # ---------------------------------------------------
                if len(hyperdata["language_iso3"])>0 and hyperdata["language_iso3"][0] != "unknown" :
                    hyperdata["language_iso3"] = hyperdata["language_iso3"][0]

                # default value = eng
                # possible even better: langid.classify(abstract)
                else:
                    # NB 97% des docs istex sont eng donc par défaut
                    # ----------------------------------------------
                    hyperdata["language_iso3"] = "eng"
                    # (cf. api.istex.fr/document/?q=*&facet=language
                    #  et  tests langid sur les language=["unknown"])
            #just to be sure
            hyperdata = self.format_hyperdata_languages(hyperdata)

            if "publication_date" in hyperdata:
                RealDate = hyperdata["publication_date"]
                if "publication_date" in hyperdata:
                    hyperdata.pop("publication_date")

                if isinstance(RealDate, list):
                    RealDate = RealDate[0]

                # print( RealDate ," | length:",len(RealDate))
                Decision = True
                if len(RealDate)>4:
                    if len(RealDate)>8:
                        try: Decision = datetime.strptime(RealDate, '%Y-%b-%d').date()
                        except:
                            try: Decision = datetime.strptime(RealDate, '%Y-%m-%d').date()
                            except: Decision=False
                    else:
                        try: Decision = datetime.strptime(RealDate, '%Y-%b').date()
                        except:
                            try: Decision = datetime.strptime(RealDate, '%Y-%m').date()
                            except: Decision=False
                else:
                    try: Decision = datetime.strptime(RealDate, '%Y').date()
                    except: Decision=False

                if Decision!=False:
                    hyperdata["publication_year"] = str(Decision.year)
                    hyperdata["publication_month"] = str(Decision.month)
                    hyperdata["publication_day"] = str(Decision.day)
                    hyperdata_list.append(hyperdata)
                    # print("\t||",hyperdata["title"])
                    # print("\t\t",Decision)
                    # print("=============================")
                # else:
                #     suma+=1
                #     if "pubdate" in json_doc:
                #         print ("\tfail pubdate:",json_doc["pubdate"])


        # print ("nb_hits:",len(json_docs))
        # print("\t - nb_fails:",suma)
        # print("  -- - - - - - -- - -")

        return hyperdata_list
