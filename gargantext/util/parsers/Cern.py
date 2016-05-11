from ._Parser import Parser
from datetime import datetime
from bs4 import BeautifulSoup
#from io import BytesIO
from io import StringIO
import json
from lxml import etree

class CernParser(Parser):
    MARC21 = {
            "100":{"a": "author_name",
                        "v": "author_affiliation",
                        "w": "author_country",
                        "m": "author_mail",
                        },
            "700": {"a": "coauthor_name",
                    "v": "coauthor_affiliation",
                    "w": "coauthor_country",
                    },
            "773":{ "c": "pages",
                    "n": "issue",
                    "p": "journal",
                    "v": "volume",
                    "y": "year"
                    },
            "024": {"a":"DOI"},
            "037": {"a":"ArXiv"},
            "022": {"a":"ISSN"},
            "245": {"a":"Title"},
            "520": {"a":"Abstract"},
            "260": {"b":"Publisher","c":"Pubdate"},
            "024": {"t":"Date"},
            "540": {"a":"Licence"},
            "653": {"a":"keywords"},
            "856": {"u":"pdf_source"},
            }

    def parse(self, filebuf):
        doc = etree.parse(filebuf)
        tree = etree.tostring(doc)
        #parser = etree.XMLParser()
        hyperdata_list =[]
        soup = BeautifulSoup(tree, "lxml")
        for record in soup.find_all("record"):

            r = {v:[] for v in self.MARC21["700"].values()}
            r["uid"]  = soup.find("controlfield").text
            for data in soup.find_all("datafield"):
                tag = data.get("tag")
                if tag in self.MARC21.keys():
                    for sub in data.find_all("subfield"):
                        code = sub.get("code")
                        if code in self.MARC21[tag].keys():
                            if tag == "700":
                                r[self.MARC21[tag][code]].append(sub.text)
                            else:
                                r[self.MARC21[tag][code]] = sub.text
            records.append(r.decode('utf-8'))


