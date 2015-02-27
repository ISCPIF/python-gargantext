from django.db import transaction
from lxml import etree
from .FileParser import FileParser
from ..NgramsExtractors import *
from datetime import datetime
from io import BytesIO

class PubmedFileParser(FileParser):
    
    def _parse(self, file):
        # open the file as XML
        xml_parser = etree.XMLParser(resolve_entities=False, recover=True)
        
        xml = ""
        if type(file)==bytes: xml = etree.parse( BytesIO(file) , parser=xml_parser)
        else: xml = etree.parse(file, parser=xml_parser)

        xml_articles = xml.findall('PubmedArticle')
        # initialize the list of metadata
        metadata_list = []
        # parse all the articles, one by one
        for xml_article in xml_articles:
            # extract data from the document
            metadata = {}
            metadata_path = {
                "journal"           : 'MedlineCitation/Article/Journal/Title',
                "title"             : 'MedlineCitation/Article/ArticleTitle',
                "abstract"          : 'MedlineCitation/Article/Abstract/AbstractText',
                "title2"            : 'MedlineCitation/Article/VernacularTitle',
                "language_iso3"     : 'MedlineCitation/Article/Language',
                "doi"               : 'PubmedData/ArticleIdList/ArticleId[@type=doi]',
                "realdate_full_"     : 'MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate',
                "realdate_year_"     : 'MedlineCitation/Article/Journal/JournalIssue/PubDate/Year',
                "realdate_month_"    : 'MedlineCitation/Article/Journal/JournalIssue/PubDate/Month',
                "realdate_day_"      : 'MedlineCitation/Article/Journal/JournalIssue/PubDate/Day',
                "publication_year"  : 'MedlineCitation/DateCreated/Year',
                "publication_month" : 'MedlineCitation/DateCreated/Month',
                "publication_day"   : 'MedlineCitation/DateCreated/Day',
                "authors"           : 'MedlineCitation/Article/AuthorList',
            }
            for key, path in metadata_path.items():
                try:
                    xml_node = xml_article.find(path)
                    # Authors tag
                    if key == 'authors':
                        metadata[key] = ', '.join([
                            xml_author.find('ForeName').text + ' ' + xml_author.find('LastName').text
                            for xml_author in xml_node
                        ])
                    else:
                        metadata[key] = xml_node.text

                except:
                    pass

            #Title-Decision
            Title=""
            if not metadata["title"] or metadata["title"]=="":
                if "title2" in metadata:
                    metadata["title"] = metadata["title2"]
                else: metadata["title"] = ""

            # Date-Decision
            # forge.iscpif.fr/issues/1418
            RealDate = ""
            if "realdate_full_" in metadata:
                RealDate = metadata["realdate_full_"]
            else:
                if "realdate_year_" in metadata: RealDate+=metadata["realdate_year_"]
                if "realdate_month_" in metadata: RealDate+=" "+metadata["realdate_month_"]
                if "realdate_day_" in metadata: RealDate+=" "+metadata["realdate_day_"]
            metadata["realdate_full_"] = RealDate
            RealDate = RealDate.split("-")[0]

            PubmedDate = ""
            if "publication_year" in metadata: PubmedDate+=metadata["publication_year"]
            if "publication_month" in metadata: PubmedDate+=" "+metadata["publication_month"]
            if "publication_day" in metadata: PubmedDate+=" "+metadata["publication_day"]

            Decision=""
            if len(RealDate)>4:
                if len(RealDate)>8:
                    try: Decision = datetime.strptime(RealDate, '%Y %b %d').date()
                    except: 
                        try: Decision = datetime.strptime(PubmedDate, '%Y %m %d').date()
                        except: Decision=False
                else: 
                    try: Decision = datetime.strptime(RealDate, '%Y %b').date()
                    except: 
                        try: Decision = datetime.strptime(PubmedDate, '%Y %m %d').date()
                        except: Decision=False
            else: 
                try: Decision = datetime.strptime(PubmedDate, '%Y %m %d').date()
                except: Decision=False

            if Decision!=False:
                if "publication_year" in metadata: metadata["publication_year"] = str(Decision.year)
                if "publication_month" in metadata: metadata["publication_month"] = str(Decision.month)
                if "publication_day" in metadata: metadata["publication_day"] = str(Decision.day)
                if "realdate_year_" in metadata: metadata.pop("realdate_year_")
                if "realdate_month_" in metadata: metadata.pop("realdate_month_")
                if "realdate_day_" in metadata: metadata.pop("realdate_day_")
                if "title2" in metadata: metadata.pop("title2")
                
                # print(metadata)
                # print("* * * * ** * * * * ")
                metadata_list.append(metadata)
        # return the list of metadata
        return metadata_list
