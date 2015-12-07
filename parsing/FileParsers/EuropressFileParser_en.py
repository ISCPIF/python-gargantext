
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

class EuropressFileParser_en(FileParser):
    def _parse(self, file):
        localeEncoding          = "fr_FR"
        codif                   = "UTF-8"
        format_page             = re.compile('p\. .*', re.UNICODE)
        
        def parse_date(date, lang):
            d = dateparser.parse(date.strip(), languages=[lang])
            return d

        if isinstance(file, str):
            file = open(file, 'rb')
        
        contents = file.read()
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
        title_xpath     = "./header/div[@class='titreArticle']"
        text_xpath      = "./section/div[@class='DocText']//p"
        

        def scrap_text(data_xpath):
            """
            Récupère le texte de toute arborescence
            sous une liste de noeuds (par ex liste de <p>)
            et renvoie une liste de string
            """
            result = list()
            
            # a priori un seul titre ou plusieurs p dans data_xpath
            for elem in data_xpath:
                all_text = list()
                # on utilise itertext pour avoir
                # tous les sous éléments 1 fois
                # quelque soit la profondeur
                for sub_txt in elem.itertext(with_tail=True):
                    sub_txt_clean = sub_txt.strip()
                    if sub_txt_clean != '':
                        all_text.append(sub_txt_clean)
                result.append(" ".join(all_text))
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
                    # attention en anglais la date contient 1 ou 2 virgules
                    # ex: "Tuesday, November 7, 2012" 
                    # ==> dans tous ces cas 'en' dateparser.parse 
                    #     sera lancé sur header[i:] et non header[i]
                    header = header.split(', ')
                    header = list(filter(lambda x: format_page.match(x) is None, header))
                    if parse_date(header[0], 'en') is not None:
                        date = ' '.join(header[0:])
                    elif parse_date(header[1], 'en') is not None:
                        hyperdata['rubrique']   = header[0]
                        date = ' '.join(header[1:])
                    elif parse_date(header[2], 'en') is not None:
                        hyperdata['rubrique']   = header[0]
                        date = ' '.join(header[2:])
                    elif parse_date(header[3], 'en') is not None:
                        hyperdata['rubrique']   = header[0]
                        date = ' '.join(header[3:])
                    else: 
                        date = '2016'

                
                try:
                    hyperdata['publication_date'] = dateparser.parse(date.strip(), languages=['en'])
                    
                except:
                    hyperdata['publication_date'] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                
                try:
                    hyperdata['publication_year']  = hyperdata['publication_date'].strftime('%Y')
                    hyperdata['publication_month'] = hyperdata['publication_date'].strftime('%m')
                    hyperdata['publication_day']  = hyperdata['publication_date'].strftime('%d')
                except:
                    print(hyperdata['title'])
                    print(date)

                try:
                    title   = scrap_text(html_article.xpath(title_xpath))
                    hyperdata['title'] = title[0]
                except:
                    pass
                                
                try:
                    text    = scrap_text(html_article.xpath(text_xpath))
                    hyperdata['abstract'] = '\n'.join([ '<p>\n'+p_text+'</p>\n' for p_text in title[1:] + text])
                    
                except:
                    pass

                yield hyperdata

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

