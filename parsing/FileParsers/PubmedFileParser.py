from django.db import transaction
from lxml import etree
from parsing.FileParsers.FileParser import FileParser
from parsing.NgramsExtractors import *

class PubmedFileParser(FileParser):
    
    def _parse(self, parentNode, file):
        # open the file as XML
        xml_parser = etree.XMLParser(resolve_entities=False, recover=True)
        xml = etree.parse(file, parser=xml_parser)
        xml_articles = xml.findall('PubmedArticle')
        with transaction.atomic():
            # initialize the list of documents
            documents = []
            # parse all the articles, one by one
            # all database operations should be performed within one transaction
            for xml_article in xml_articles:
                # extract data from the document
                metadata = {}
                metadata_path = {
                    "journal"           : 'MedlineCitation/Article/Journal/Title',
                    "title"             : 'MedlineCitation/Article/ArticleTitle',
                    "language_iso3"     : 'MedlineCitation/Article/Language',
                    "doi"               : 'PubmedData/ArticleIdList/ArticleId[@type=doi]',
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
                    metadata    = metadata,
                    #guid        = metadata["doi"],
                )
                if document:
                    documents.append(document)
            # return the list of documents
            return documents
