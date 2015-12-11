"""
Parses Europress 2015 html format (both for english and french)
 => recognizes language according to date format
 => scraps text for each paragraph to fill hyperdata['abstract']
"""

__author__    = "Gargantext Team"
__copyright__ = "Copyright 2014-15 ISCPIF-CNRS"
__version__   = "0.1"
__email__     = "romain.loth@iscpif.fr"
__status__    = "Test"

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
        #print("europr_parser file", file)
        
        localeEncoding          = "fr_FR"
        codif                   = "UTF-8"
        format_page             = re.compile('p\. .*', re.UNICODE)
        # les docs europresse en/fr
        # se distinguent principalement
        # par la forme de leur date
        
        # ex:  November 7, 2012
        format_date_en  = re.compile(r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+[0-3]?\d,\s+(?:19|20)\d\d')
        # ex:  16 mars 2011
        format_date_fr  = re.compile(r'[0-3]?\d\s+(?:janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+(?:19|20)\d\d')
        
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
        detailed_header_xpath    = "./header/div/span[@class = 'DocHeader']"
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
                
                # print("2 en 1 ==============================new article")

                hyperdata = {}
                
                # analyse de la langue  => utile pour la date
                # faite localement pour permettre aux utilisateurs
                # de choisir ResourceType "Europress" sans s'occuper
                # du détail de la langue sourc
                doc_language = None
                
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
                
                # span de class DocHeader fournissant rubrique et date
                get_dated_header = html_article.xpath(detailed_header_xpath)
                
                # le detailed_header est occasionnellement absent
                # => FIX TEMPORAIRE: on skippe le document
                if len(get_dated_header) == 0 or get_dated_header[0].text is None:
                    print("WARNING (document skip) unformatted europress header")
                    continue
                else:
                    header = get_dated_header[0].text
                    
                    # Article detailed headers in europress
                    # --------------------------------------
                    # ex: "Seine-Saint-Denis, lundi 28 janvier 2013, p. 93_T_17"
                    # ex: "Votre ville, jeudi 6 février 2014"
                    # ex: "World, Friday, November 13, 2015"
                    
                    # 1) test language before splitting
                    
                    if re.search(format_date_fr,header):
                        doc_language = 'fr'
                        # print("=============== Header date fr")
                        
                        # save for FileParser
                        hyperdata["language_iso2"] = 'fr'
                    
                    elif re.search(format_date_en,header):
                        doc_language = 'en'
                        # print("=============== Header date en")
                        
                        # save for FileParser
                        hyperdata["language_iso2"] = 'en'
                    
                    else:
                        print("WARNING europress: echec diagnostic langue header sur '%s'" % header)
                        # default value, used locally, not saved
                        doc_language = 'en'
                    
                    # attention en anglais la date contient 1 ou 2 virgules
                    # ex: "Tuesday, November 7, 2012" 
                    # ==> dans tous ces cas 'en' dateparser.parse 
                    #     sera lancé sur header[i:] et non header[i]
                    header = header.split(', ')
                    
                    # mais dateparser ne veut pas d'éléments autres à la suite de la date
                    # ==> on filtre les indications de pages qu'europress met souvent après
                    header = list(filter(lambda x: format_page.match(x) is None, header))
                    
                    date = None
                    
                    if parse_date(header[0], doc_language) is not None:
                        if doc_language == 'fr':
                            date = header[0]
                            # print("match 1 fre => 0 = %s " % date)
                        else:
                            date = ' '.join(header[0:])
                            # print("match 0 eng => 0: = %s " % date)
                    else:
                        # most probably news_topic before beginning of date
                        hyperdata['rubrique']   = header[0]
                        
                        # [1..last_header_fragment]
                        for i in range(1,len(header)):
                            if parse_date(header[i], doc_language) is not None:
                                if doc_language == 'fr':
                                    date = header[i]
                                    # print("match %i fre => %i = %s " % (i,i,date))
                                else:
                                    date = ' '.join(header[i:])
                                    # print("match %i eng => %i: = %s " % (i,i,date))
                    
                    # default
                    if date is None:
                        date = '2016'
                        # print("no match => 2016")

                # we parse the retrieved datestring into a formal date
                try:
                    hyperdata['publication_date'] = dateparser.parse(date.strip(), doc_language)
                    # print("RES POSTPROC:",hyperdata['publication_date'])
                    
                except:
                    hyperdata['publication_date'] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                
                try:
                    hyperdata['publication_year']  = hyperdata['publication_date'].strftime('%Y')
                    hyperdata['publication_month'] = hyperdata['publication_date'].strftime('%m')
                    hyperdata['publication_day']  = hyperdata['publication_date'].strftime('%d')
                except:
                    print(hyperdata['title'])
                    print(date)
                #print(hyperdata['publication_date'])
		
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

