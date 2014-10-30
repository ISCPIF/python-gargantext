

import re
import locale
from lxml import etree
from datetime import datetime, date

from parsing.FileParsers.FileParser import FileParser
from parsing.NgramsExtractors import *



class EuropressFileParser(FileParser):
   def __init__(self):
       # Encoding
       self.codif      = "UTF-8"
       self.localeEncoding = "fr_FR"

  
   def _parse(self, file):
       count = 0
       
       html_parser = etree.HTMLParser(encoding=self.codif)
       html = etree.parse(file, html_parser)
       html_articles = html.xpath('/html/body/table')

       # initialize the list of metadata
       metadata_list = []
       # parse all the articles, one by one

       for html_article in html_articles:
           
           metadata = {}
           
           if len(html_article):
               for name in html_article.xpath("./tr/td/span[@class = 'DocPublicationName']"):
                   if name.text is not None:
                       format_journal = re.compile('(.*), (.*)', re.UNICODE)
                       test_journal = format_journal.match(name.text)
                       if test_journal is not None:
                           metadata['source'] = test_journal.group(1)
                           metadata['volume'] = test_journal.group(2)
                       else:
                           metadata['source'] = name.text.encode(self.codif)

               for header in html_article.xpath("./tr/td/span[@class = 'DocHeader']"):
                   text = header.text
                   if isinstance(text, bytes):
                       text = text.decode()

                   format_date_fr = re.compile('\d+\s*\w+\s+\d{4}', re.UNICODE)
                   test_date_fr = format_date_fr.match(text)
                   
                   format_date_en = re.compile('\w+\s+\d+,\s+\d{4}', re.UNICODE)
                   test_date_en = format_date_en.match(text)

                   format_sect = re.compile('(\D+),', re.UNICODE)
                   test_sect = format_sect.match(text)
                   
                   format_page = re.compile(', p. (\w+)', re.UNICODE)
                   test_page = format_page.match(text)
                   
                   if test_date_fr is not None:
                       self.localeEncoding = "fr_FR"
                       locale.setlocale(locale.LC_ALL, self.localeEncoding)
                       try :
                           metadata['date'] = datetime.strptime(text, '%d %B %Y')
                       except :
                           try:
                               metadata['date'] = datetime.strptime(text, '%B %Y')
                           except :
                               pass
                   
                   if test_date_en is not None:
                       self.localeEncoding = "en_GB.UTF-8"
                       locale.setlocale(locale.LC_ALL, self.localeEncoding)
                       try :
                           metadata['date'] = datetime.strptime(text, '%B %d, %Y')
                       except :
                           try :
                               metadata['date'] = datetime.strptime(text, '%B %Y')
                           except :
                               pass

                   if test_sect is not None:
                       metadata['section'] = test_sect.group(1).encode(self.codif)
                   
                   if test_page is not None:
                       metadata['page'] = test_page.group(1).encode(self.codif)

               metadata['title'] = html_article.xpath("string(./tr/td/span[@class = 'TitreArticleVisu'])").encode(self.codif)
               metadata['text']  = html_article.xpath("./tr/td/descendant-or-self::*[not(self::span[@class='DocHeader'])]/text()")
              
               line = 0
               br_tag = 10
               for i in html_articles[count].iter():
                  # print line, br, i, i.tag, i.attrib, i.tail
                   if i.tag == "span":
                       if "class" in i.attrib:
                           if i.attrib['class'] == 'TitreArticleVisu':
                               line = 1
                               br_tag = 2
                   if line == 1 and i.tag == "br":
                       br_tag -= 1
                   if line == 1 and br_tag == 0:
                       try:
                           metadata['authors'] = str.title(etree.tostring(i, method="text", encoding=self.codif)).encode(self.codif)#.split(';')
                       except:
                           metadata['authors'] = 'not found'
                       line = 0
                       br_tag = 10
               
               
               try:
                   if metadata['date'] is not None or metadata['date'] != '':
                       try:
                           back = metadata['date']
                       except Exception as e: 
                           print(e)
                           pass
                   else:
                       try:
                           metadata['date'] = back
                       except Exception as e:
                           print(e)
               except :
                   metadata['date'] = datetime.now()


               metadata['object_id'] = metadata['text'][-9]
               metadata['text'].pop()
               metadata['text'] = ' '.join(metadata['text'])
               metadata['text'] = re.sub('Tous droits réservés.*$', '', metadata['text'])

               metadata['bdd']  = 'europresse'
               metadata['url']  = ''
               
               metadata_list.append(metadata)
               count += 1
        

       return metadata_list









