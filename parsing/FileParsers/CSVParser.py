from django.db import transaction
from lxml import etree
from .FileParser import FileParser
from ..NgramsExtractors import *
from datetime import datetime
from io import BytesIO

class CSVParser(FileParser):
    
    def _parse(self, file):
        hyperdata_list = []
        print(hyperdata_list)
        print(file)

        import csv
        f = open(file , "r")
        reader = csv.reader(f)

        counter = 0
        for row in reader:
            if counter >0:
                doi = row[0]
                # ['ID', 'PI', 'AG1', 'AG2', 'ACR', 'TI', 'ABS']
                authors = row[1]
                title = row[5]
                abstract = row[6]
                agency = ""
                if row[2]!="": agency = row[2]
                else:  agency = row[3]

                pub = {}
                pub["doi"] = doi
                pub["title"] = title
                pub["journal"] = agency
                pub["abstract"] = abstract
                pub["publication_year"] = "2014"
                pub["publication_month"] = "01"
                pub["publication_day"] = "01"
                pub["authors"] = [ authors ]

                hyperdata_list.append(pub)

            else: counter+=1
        f.close()
        return hyperdata_list
