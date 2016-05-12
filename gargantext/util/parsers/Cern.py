from ._Parser import Parser
from datetime import datetime
from bs4 import BeautifulSoup
#from io import BytesIO
from io import StringIO
import json
from lxml import etree

class CernParser(Parser):
    #mapping MARC21 ==> hyperdata
    MARC21 = {
            #here main author
            "100":{
                    "a": "author_name",
                    "v": "author_affiliation",
                    "w": "author_country",
                    "m": "author_mail",
                    },
            #here cooauthor
            "700": {
                    "a": "authors_name",
                    "v": "authors_affiliation",
                    "w": "authors_country",
                    },
            "773":{
                    "c": "pages",
                    "n": "issue",
                    "p": "journal",
                    "v": "volume",
                    "y": "year"
                    },
            "024": {"a":"doi"},
            "037": {"a":"arxiv"},
            "022": {"a":"isbn"},
            "245": {"a":"title"},
            "520": {"a":"abstract"},
            "260": {"b":"publisher","c":"pubdate"},
            #"024": {"t":"date"},
            #"540": {"a":"licence"},
            #"653": {"a":"keywords"},
            #"856": {"u":"pdf_source"},
            }
    #~ hyperdata_item = {
        #~ "journal"           : '',
        #~ "title"             : '',
        #~ "abstract"          : '',
        #~ "title"            : '',
        #~ "language_iso2"     : 'en',
        #~ "doi"               : '',
        #~ "realdate_full_"     : '',
        #~ "realdate_year_"     : '',
        #~ "realdate_month_"    : '',
        #~ "realdate_day_"      : '',
        #~ "publication_year"  : '',
        #~ "publication_month" : '',
        #~ "publication_day"   : '',
        #~ "authors"           : '',
        #~ "authors_countries" : '',
        #~ "authors_affiliations": '',
        #~ "publisher": '',
    #~ }

    def parse(self, file):
        if isinstance(file, str):
            file = open(file, 'rb')
        doc = etree.parse(file.read())
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
                            if tag == "100":
                                r[self.MARC21["700"][code]].insert(0,sub.text)
                            else:
                                r[self.MARC21[tag][code]] = sub.text
            print(r)
            #hyperdata_list.append(r["uid.decode('utf-8'))
            break
        return hyperdata_list

if __name__ == "__main__":
    pass
    #~ e = CernParser()
    #~ hyperdata = e.parse(str(sys.argv[1]))
    #~ for h in hyperdata:
        #~ try:
            #~ print(h['journal'], ":", h['publication_date'])
        #~ except:
            #~ pass
        #~ break
