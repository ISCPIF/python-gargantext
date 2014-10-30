from django.db import transaction
from lxml import etree
from parsing.FileParsers.FileParser import FileParser
from parsing.NgramsExtractors import *
import zipfile
import datetime

class PubmedFileParser(FileParser):
    
    def parse(self, parentNode=None, tag=True):
        # open the file as XML
        xml_parser = etree.XMLParser(resolve_entities=False, recover=True)
        documents = []

        with transaction.atomic():
            with zipfile.ZipFile(self._file) as zipFile:
                for filename in zipFile.namelist():
                    file = zipFile.open(filename, "r")
                    xml = etree.parse(file, parser=xml_parser)

                    # parse all the articles, one by one
                    # all database operations should be performed within one transaction
                    xml_articles = xml.findall('PubmedArticle')
                    for xml_article in xml_articles:
                        # extract data from the document
                        metadata = {}
                        metadata_path = {
                            "journal"           : 'MedlineCitation/Article/Journal/Title',
                            "title"             : 'MedlineCitation/Article/ArticleTitle',
                            "language_iso3"     : 'MedlineCitation/Article/Language',
                            "doi"               : 'PubmedData/ArticleIdList/ArticleId[type=doi]',
                            "abstract"          : 'MedlineCitation/Article/Abstract/AbstractText',
                            "publication_year"  : 'MedlineCitation/DateCreated/Year',
                            "publication_month" : 'MedlineCitation/DateCreated/Month',
                            "publication_day"   : 'MedlineCitation/DateCreated/Day',
                        }
                        for key, path in metadata_path.items():
                            try:
                                node = xml_article.find(path)
                                metadata[key] = node.text
                            except:
                                metadata[key] = ""
                        contents    = metadata["abstract"]
                        # create the document in the database
                        document    = self.create_document(
                            parentNode  = parentNode,
                            title       = metadata["title"],
                            contents    = contents,
                            language    = self._languages_iso3[metadata["language_iso3"].lower()],
                            metadata    = metadata,
                            #guid        = metadata["doi"],
                        )
                        if document:
                            documents.append(document)
        return documents
