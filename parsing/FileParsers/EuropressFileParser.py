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

        # all except detail_header are mandatory to parse the article
        name_xpath  = "./header/div/span[@class = 'DocPublicationName']"
        
        # title_xpath (cas normal):
        #         "./header/div[@class='titreArticle']"
        # title_xpath (rapports):
        #         "./header/div/p[@class='titreArticleVisu grandTitre']"
        #
        # title_xpath (chemin plus générique)
        title_xpath         = "./header//*[contains(@class,'titreArticle')]"
        text_xpath          = "./section/div[@class='DocText']//p"
        entire_header_xpath = "./header"
        
        # diagnosed during date retrieval and used for rubrique
        detail_header_xpath = "./header/div/span[@class = 'DocHeader']"
        

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
                
                # print("==============================new article")
                
                # s'il n'y a pas du tout de header on doit skip
                all_header = html_article.xpath(entire_header_xpath)
                if len(all_header) == 0:
                    print("WARNING: europress (skip) article without header")
                    continue
                
                hyperdata = {}
                
                
                # TITLE
                # -----
                title = []
                try:
                    title   = scrap_text(html_article.xpath(title_xpath))
                    hyperdata['title'] = title[0]
                except:
                    # il y aura un problème d'affichage si pas de titre !
                    print("WARNING: europress (skip) article without title")
                    continue
                
                
                # FULLTEXT
                # --------
                try:
                    text    = scrap_text(html_article.xpath(text_xpath))
                    hyperdata['abstract'] = '\n'.join([ '<p>'+p_text+'</p>' for p_text in title[1:] + text])
                    
                except:
                    pass
                
                # PUBLICATIONNAME
                # ----------------
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
                
                
                # DATE et LANGUAGE
                # ----------------
                # analyse locale de la langue via le format de la date
                # 
                # permet de choisir ResourceType "Europress" sans s'occuper
                # du détail de la langue source
                doc_language = None
                date = None
                
                # le texte sur lequel on cherchera la date/langue
                search_text = None
                
                # zone DocHeader fournissant précisément rubrique et date
                detailed_text = None
                get_detail_header = html_article.xpath(detail_header_xpath)
                
                if len(get_detail_header) != 0:
                    # cas le plus courant
                    # -------------------
                    # ex: "Seine-Saint-Denis, lundi 28 janvier 2013, p. 93_T_17"
                    # ex: "Votre ville, jeudi 6 février 2014"
                    # ex: "World, Friday, November 13, 2015"
                    detailed_text = get_detail_header[0].text
                    search_text = detailed_text
                
                else:
                    # occasionellment DocHeader absent
                    # (on se rabat sur le header entier)
                    search_text = " ".join(scrap_text(all_header[0]))
                    
                    # print("---using all header: '%s'" % search_text)
                
                
                # on poursuit date/langue avec la zone obtenue
                
                # 1) Une REGEXP identifie la langue ET attrape la date
                test_date_fr = re.search(format_date_fr,search_text)
                
                if test_date_fr:
                    doc_language = 'fr'
                    # print("=============== Header date fr")
                    
                    # save for FileParser
                    hyperdata["language_iso2"] = 'fr'
                    
                    # match str
                    date_str = test_date_fr.group()
                
                else:
                    # ex:  November 7, 2012
                    test_date_en = re.search(format_date_en,search_text)
                
                    if test_date_en:
                        doc_language = 'en'
                        # print("=============== Header date en")
                        
                        # save for FileParser
                        hyperdata["language_iso2"] = 'en'
                        # match str
                        date_str = test_date_en.group()
                    else:
                        print("WARNING europress: echec diagnostic date/langue header sur '%s'" % header)
                        # default lg value, used locally, not saved
                        doc_language = 'en'
                        # default date value, will be saved
                        date_str = "2016"
                
                # 2) we parse the retrieved datestring into a formal date
                try:
                    hyperdata['publication_date'] = dateparser.parse(
                     date_str.strip(), 
                     languages=[doc_language],
                     date_formats=['%d %B %Y','%B %d, %Y']
                     )
                    # print("RES POSTPROC:",hyperdata['publication_date'])
                    
                except:
                    hyperdata['publication_date'] = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
                
                
                
                # infos dérivées
                hyperdata['publication_year']  = hyperdata['publication_date'].strftime('%Y')
                hyperdata['publication_month'] = hyperdata['publication_date'].strftime('%m')
                hyperdata['publication_day']  = hyperdata['publication_date'].strftime('%d')
                
                
                # RUBRIQUE
                # --------
                # quand on a le DocHeader détaillé on peut vérifier la rubrique
                # (si présente elle est juste avant la date)
                if detailed_text is not None:
                    header_elts = detailed_text.split(', ')
                    # on vérifie que le premier élément n'est pas une date ou un fragment de date
                    if parse_date(header_elts[0], doc_language) is None:
                        # most probably news_topic before beginning of date
                        hyperdata['rubrique']   = header_elts[0]
                
                
                yield hyperdata

        except:
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

