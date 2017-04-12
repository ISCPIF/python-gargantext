from ._Parser import Parser
from datetime import datetime
import json

class MultivacParser(Parser):

    def parse(self, filebuf):
        '''
        parse :: FileBuff -> [Hyperdata]
        '''
        contents = filebuf.read().decode("UTF-8")
        data = json.loads(contents)
        
        filebuf.close()
        
        json_docs = data
        hyperdata_list = []
        
        hyperdata_path = {
            "id"                : "id",
            "title"             : "title",
            "abstract"          : "abstract",
            "type"              : "type"
        }

        suma = 0
        
        for json_doc in json_docs:

            hyperdata = {}
            
            doc = json_doc["_source"]

            for key, path in hyperdata_path.items():
                    hyperdata[key] = doc.get(path, "")
            
            hyperdata["source"] = doc.get("serial"      , {})\
                                     .get("journaltitle", "REPEC Database")
            
            try:
                hyperdata["url"]    = doc.get("file", {})\
                                         .get("url" , "")
            except:
                pass

            hyperdata["authors"] = ", ".join(
                                             [ p.get("person", {})
                                                .get("name"  , "")
                          
                                               for p in doc.get("hasauthor", [])
                                             ]
                                            )
            

            year = doc.get("serial"  , {})\
                      .get("issuedate", None)
            
            if year == "Invalide date":
                year = doc.get("issuedate"  , None)

            if year is None:
                year = datetime.now()
            else:
                try:
                    date = datetime.strptime(year, '%Y')
                except:
                    print("FIX DATE MULTIVAC REPEC %s" % year)
                    date = datetime.now()

            hyperdata["publication_date"] = date
            hyperdata["publication_year"]  = str(date.year)
            hyperdata["publication_month"] = str(date.month)
            hyperdata["publication_day"]   = str(date.day)
            
            hyperdata_list.append(hyperdata)
        
        return hyperdata_list
