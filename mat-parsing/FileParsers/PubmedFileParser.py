from django.db import transaction
from FileParser import FileParser


class PubmedFileParser(FileParser):
    
    def parse(self, parentNode):
        # open the file as XML
        xml_parser = etree.XMLParser(resolve_entities=False,recover=True)
        xml = etree.parse(self._file, parser=xml_parser)
        # parse all the abstracts
        # all database operations should be performed within one transaction
        xml_articles = xml.findall('PubmedArticle')
        with transaction.atomic():
            for xml_article in xml_articles:
                # extract data from the document
                date_year   = int(xml_article.find('MedlineCitation/DateCreated/Year').text)
                date_month  = int(xml_article.find('MedlineCitation/DateCreated/Month').text)
                date_day    = int(xml_article.find('MedlineCitation/DateCreated/Day').text)
                metadata    = {
                    "date":     datetime.date(year, month, day),
                    "journal":  xml_article.find('MedlineCitation/Article/Journal/Title').text
                    "title":    xml_article.find('MedlineCitation/Article/ArticleTitle').text
                    "doi":      xml_article.find('PubmedData/ArticleIdList/ArticleId[type=doi]')
                    # other metadata should also be included: submission date, etc.
                }
                contents    = xml_article.find('MedlineCitation/Article/Abstract/AbstractText').text
                # create the document in the database
                childNode   = 
                childNode
