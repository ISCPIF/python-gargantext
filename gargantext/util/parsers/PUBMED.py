from lxml import etree
from ._Parser import Parser
from datetime import datetime
from io import BytesIO


class PubmedParser(Parser):

    hyperdata_path = {
        "source"            : 'MedlineCitation/Article/Journal/Title',
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

    # xml_parser = etree.XMLParser(resolve_entities=False, recover=True)
    xml_parser = etree.XMLParser(resolve_entities=False, recover=True)

    def parse(self, file):
        # open the file as XML
        if isinstance(file, bytes):
            file = BytesIO(file)
        xml = etree.parse(file, parser=self.xml_parser)
        #print(xml.find("PubmedArticle"))
        xml_articles = xml.findall('PubmedArticle')
        # initialize the list of hyperdata
        hyperdata_list = []
        # parse all the articles, one by one
        for xml_article in xml_articles:
            # extract data from the document
            hyperdata = {}
            for key, path in self.hyperdata_path.items():
                try:
                    xml_node = xml_article.find(path)
                    # Authors tag
                    if key == 'authors':
                        hyperdata[key] = ', '.join([
                            xml_author.find('ForeName').text + ' ' + xml_author.find('LastName').text
                            for xml_author in xml_node
                        ])
                    else:
                        hyperdata[key] = xml_node.text

                except:
                    pass

            #Title-Decision
            Title=""
            if not hyperdata["title"] or hyperdata["title"]=="":
                if "title2" in hyperdata:
                    hyperdata["title"] = hyperdata["title2"]
                else: hyperdata["title"] = ""

            # Date-Decision
            # forge.iscpif.fr/issues/1418
            RealDate = ""
            if "realdate_full_" in hyperdata:
                RealDate = hyperdata["realdate_full_"]
            else:
                if "realdate_year_" in hyperdata: RealDate+=hyperdata["realdate_year_"]
                if "realdate_month_" in hyperdata: RealDate+=" "+hyperdata["realdate_month_"]
                if "realdate_day_" in hyperdata: RealDate+=" "+hyperdata["realdate_day_"]
            hyperdata["realdate_full_"] = RealDate
            RealDate = RealDate.split("-")[0]

            PubmedDate = ""
            if "publication_year" in hyperdata: PubmedDate+=hyperdata["publication_year"]
            if "publication_month" in hyperdata: PubmedDate+=" "+hyperdata["publication_month"]
            if "publication_day" in hyperdata: PubmedDate+=" "+hyperdata["publication_day"]

            Decision=True
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
                if "publication_year" in hyperdata: hyperdata["publication_year"] = str(Decision.year)
                if "publication_month" in hyperdata: hyperdata["publication_month"] = str(Decision.month)
                if "publication_day" in hyperdata: hyperdata["publication_day"] = str(Decision.day)
                if "realdate_year_" in hyperdata: hyperdata.pop("realdate_year_")
                if "realdate_month_" in hyperdata: hyperdata.pop("realdate_month_")
                if "realdate_day_" in hyperdata: hyperdata.pop("realdate_day_")
                if "title2" in hyperdata: hyperdata.pop("title2")

                hyperdata_list.append(hyperdata)
        # return the list of hyperdata
        return hyperdata_list
