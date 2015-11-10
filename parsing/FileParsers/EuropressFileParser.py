
import re
import locale

from lxml import etree
from lxml.etree import tostring
from lxml.html import html5parser
from itertools import chain

from datetime import datetime, date
from django.utils import timezone
import dateutil.parser
import dateparser

import sys
#sys.path.append('/srv/gargantext')
#from admin.env import *
#from parsing.FileParsers.FileParser import FileParser
from .FileParser import FileParser
#from parsing.NgramsExtractors import *
from ..NgramsExtractors import *

from admin.utils import PrintException

class EuropressFileParser(FileParser):
    def _parse(self, file):
        localeEncoding = "fr_FR"
        codif      = "UTF-8"
        format_date = re.compile('.*\d{4}.*', re.UNICODE)

        if isinstance(file, str):
            file_open = open(file, 'rb')
        
        contents = file_open.read()
        encoding = self.detect_encoding(contents)
        
        if encoding != "utf-8":
            try:
                contents = contents.decode("latin1", errors='replace').encode(codif)
            except:
                PrintException()

        html_parser = etree.HTMLParser(encoding=codif)
        html = etree.fromstring(contents, html_parser)

        html_parser = html5parser.etree.HTMLParser(encoding=codif)
        html = html5parser.etree.fromstring(contents, html_parser)
        html_articles = html.xpath('//article')


        name_xpath      = "./header/div/span[@class = 'DocPublicationName']"
        header_xpath    = "./header/div/span[@class = 'DocHeader']"
        title_xpath     = "./header/div[@class='titreArticle']/descendant-or-self::*"
        text_xpath      = "./section/div[@class='DocText']/descendant-or-self::*"
        

        def paragraph_list(data_xpath):
            result = list()
            for elem in data_xpath:
                if elem.text is not None:
                    if elem.text.strip() != '':
                        if elem.tag == 'p':
                            result.append(elem.text)
                        else:
                            if len(result) > 0:
                                result.append(result.pop() + elem.text)
                            else:
                                result.append(elem.text)
            return result

        # parse all the articles, one by one
        try:
            for html_article in html_articles:

                hyperdata = {}
                
                try:
                    pub_name = html_article.xpath(name_xpath)[0].text
                    name = pub_name.split(', ')
                    hyperdata['journal']    =  name[0]
                    hyperdata['number']     =  name[1]
                except:
                    try:
                        hyperdata['journal']    =  pub_name.strip()
                    except:
                        pass
                    
                
                header = html_article.xpath(header_xpath)[0].text
                if header is not None:
                    header = header.split(', ')
                    if format_date.match(header[0]):
                        date       = header[0]
                    else:
                        hyperdata['rubrique']   = header[0]
                        date       = header[1]

                    try:
                        hyperdata['page']       = header[2].split(' ')[1]
                    except:
                        pass
                try:
                    hyperdata['publication_date'] = dateparser.parse(date, languages=['fr', 'en'])
                except:
                    hyperdata['publication_date'] = timezone.now()
                
                try:
                    title   = paragraph_list(html_article.xpath(title_xpath))
                    hyperdata['title'] = title[0]
                except:
                    pass
                
                try:
                    text    = paragraph_list(html_article.xpath(text_xpath))
                    hyperdata['abstract'] = ' '.join([ ' <p> ' + p + ' </p> ' for p in title[1:] + text])
                except:
                    pass

                yield hyperdata

            file_open.close()

        except :
            PrintException()
            pass

if __name__ == "__main__":
    e = EuropressFileParser()
    hyperdata = e.parse(str(sys.argv[1]))
    for h in hyperdata:
        try:
            print(h['journal'], ":", h['publication_date'])
        except:
            pass


