from django.db import transaction
from lxml import etree
from parsing.FileParsers.FileParser import FileParser
import zipfile
import datetime

class PubmedFileParser(FileParser):
    
    def parse(self, parentNode, tag=True):
        # open the file as XML
        xml_parser = etree.XMLParser(resolve_entities=False, recover=True)
        documents = []

        with transaction.atomic():
            with zipfile.ZipFile(self._file) as zipFile:
                for filename in zipFile.namelist():
                    file = zipFile.open(filename, "r")
#                    print(file.read())
                    xml = etree.parse(file, parser=xml_parser)

                    # parse all the articles, one by one
                    # all database operations should be performed within one transaction
                    xml_articles = xml.findall('PubmedArticle')
                    for xml_article in xml_articles:
                        # extract data from the document
                        date_year   = int(xml_article.find('MedlineCitation/DateCreated/Year').text)
                        date_month  = int(xml_article.find('MedlineCitation/DateCreated/Month').text)
                        date_day    = int(xml_article.find('MedlineCitation/DateCreated/Day').text)
                        metadata    = {
                            # other metadata should also be included:
                            # authors, submission date, etc.
                            "date_pub":      datetime.date(date_year, date_month, date_day),
                            "journal":       xml_article.find('MedlineCitation/Article/Journal/Title').text,
                            "title":         xml_article.find('MedlineCitation/Article/ArticleTitle').text,
                            "language_iso3": xml_article.find('MedlineCitation/Article/Language').text,
#                            "doi":           xml_article.find('PubmedData/ArticleIdList/ArticleId[type=doi]').text
                            "doi": "poiopipoiopip"
                        }
                        contents    = xml_article.find('MedlineCitation/Article/Abstract/AbstractText').text
                        # create the document in the database
                        document    = self.create_document(
                            parentNode  = parentNode,
                            title       = metadata["title"],
                            contents    = contents,
                            language    = self._languages_iso3[metadata["language_iso3"].lower()],
                            metadata    = metadata,
                            guid        = metadata["doi"],
                        )
                        if document:
                            documents.append(document)
        return documents
