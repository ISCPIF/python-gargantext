from django.db import transaction
from lxml import etree
from .FileParser import FileParser
from ..NgramsExtractors import *

from collections import defaultdict

class PubmedFileParser(FileParser):
    
    def _parse(self, file):
        # open the file as XML
        xml_parser = etree.XMLParser(resolve_entities=False, recover=True)
        xml = etree.parse(file, parser=xml_parser)
        xml_articles = xml.findall('PubmedArticle')
        # parse all the articles, one by one
        for xml_article in xml_articles:
            # extract data from the document
            metadata = defaultdict(str)
            metadata_path = {
                "journal"           : 'MedlineCitation/Article/Journal/Title',
                "title"             : 'MedlineCitation/Article/ArticleTitle',
                "language_iso3"     : 'MedlineCitation/Article/Language',
                "doi"               : 'PubmedData/ArticleIdList/ArticleId[@type=doi]',
                "abstract"          : 'MedlineCitation/Article/Abstract/AbstractText',
                "publication_year"  : 'MedlineCitation/DateCreated/Year',
                "publication_month" : 'MedlineCitation/DateCreated/Month',
                "publication_day"   : 'MedlineCitation/DateCreated/Day',
                "authors"           : 'MedlineCitation/Article/AuthorList',
            }
            for key, path in metadata_path.items():
                try:
                    xml_node = xml_article.find(path)
                    if key == 'authors':
                        metadata[key] = ', '.join([
                            xml_author.find('ForeName').text + ' ' + xml_author.find('LastName').text
                            for xml_author in xml_node
                        ])
                    else:
                        if metadata[key]:
                            metadata[key] += '\n'
                        metadata[key] += xml_node.text
                except:
                    pass
            yield metadata
