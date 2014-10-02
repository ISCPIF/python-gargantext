#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" 
Europresse Database parser for HTML sources only. 

This script is using 3 methods of parsing:

    1) REGEX (Regular Expressions) format detection
    2) SAX (Simple Api for Xml) like method for events detection
    3) DOM (Document Object Model), operating on the document as a whole for
    tree detection.

Bug reports? Please contact the author:
__author__ : alexandre+gargantext @ delanoe.org
__licence__ : GPL version 3.0+
__DATE__ : 09 november 2013
__VERSION__ : 2.0
"""

import os
import sys
import imp
imp.reload(sys)
import re

import locale

from datetime import datetime, date
from lxml import etree

from documents.models import Document
#from .corpus import Corpus

class Europresse():
    """
    1) First build tree to parse data
    2) Then each notice (article) is nested in a dictionary,
    3) Finaly, corpus is a list of articles as dictionnaries.
    """

    def __init__(self):
        """self.corpus is a list
        articles is the list of articles in the HTML page
        article is an article as dict"""

        # Specific declarations for Europresse
        self.data       = []

        # Encoding
        self.codif      = "UTF-8"
        self.localeEncoding = "fr_FR"

    def test_unicode(self, filename):
        import os
        os.system("file_europresse=$(mktemp -q); file --mime-encoding \'%s\' | grep -i -- \"iso-8859\" && \
                iconv -f latin1 -t utf8 \'%s\' > $file_europresse && \
                mv $file_europresse \'%s\'" % (filename, filename, filename))

    def parse(self, filename):
        """Adding filename to self.data after parsing"""
        count = 0
        articles   = []
        article    = {}

        parser = etree.HTMLParser(encoding=self.codif)
        tree = etree.parse(filename, parser)
        articles = tree.xpath('/html/body/table')

        for notice in articles:
            if len(notice):
                for name in notice.xpath("./tr/td/span[@class = 'DocPublicationName']"):
                    if name.text is not None:
                        format_journal = re.compile('(.*), (.*)', re.UNICODE)
                        test_journal = format_journal.match(name.text)
                        if test_journal is not None:
                            article['source'] = test_journal.group(1)
                            article['volume'] = test_journal.group(2)
                        else:
                            article['source'] = name.text.encode(self.codif)

                for header in notice.xpath("./tr/td/span[@class = 'DocHeader']"):
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
                            article['date'] = datetime.strptime(text, '%d %B %Y')
                        except :
                            try:
                                article['date'] = datetime.strptime(text, '%B %Y')
                            except :
                                pass
                    
                    if test_date_en is not None:
                        self.localeEncoding = "en_GB.UTF-8"
                        locale.setlocale(locale.LC_ALL, self.localeEncoding)
                        try :
                            article['date'] = datetime.strptime(text, '%B %d, %Y')
                        except :
                            try :
                                article['date'] = datetime.strptime(text, '%B %Y')
                            except :
                                pass

                    if test_sect is not None:
                        article['section'] = test_sect.group(1).encode(self.codif)
                    
                    if test_page is not None:
                        article['page'] = test_page.group(1).encode(self.codif)

                article['title'] = notice.xpath("string(./tr/td/span[@class = 'TitreArticleVisu'])").encode(self.codif)
                article['text'] = notice.xpath("./tr/td/descendant-or-self::*[not(self::span[@class='DocHeader'])]/text()")
               
                line = 0
                br_tag = 10
                for i in articles[count].iter():
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
                            article['authors'] = str.title(etree.tostring(i, method="text", encoding=self.codif)).encode(self.codif)#.split(';')
                        #article['authors'] = tuple(article['authors'])
                        except:
                            article['authors'] = 'not found'
                        line = 0
                        br_tag = 10
                
                
                try:
                    if article['date'] is not None or article['date'] != '':
                        try:
                            back = article['date']
                        except Exception as e: 
                            print(e)
                            pass
                    else:
                        try:
                            article['date'] = back
                        except Exception as e:
                            print(e)
                except :
                    article['date'] = datetime.now()


                article['uniqu_id'] = article['text'][-9]
                article['text'].pop()
                article['text'] = ' '.join(article['text'])
                article['text'] = re.sub('Tous droits réservés.*$', '', article['text'])

                article['bdd']  = 'europresse'
                article['url']  = ''
                
                self.data.append(article)
                article = {'source': "", 'volume': "", 'date': "", \
                        'authors': "", 'section': "", 'page':"", 'text': "", 'object_id':""}
                count += 1

    def add(self, project=None, corpus=None, user=None, ids=None):
        """ Appends notices to self.corpus from self.data removing duplicates"""
        if ids is not None:
            self.object_ids = ids
        else:
            self.object_ids = set()
        
        for i in self.data:
            if i['uniqu_id'] not in self.object_ids and isinstance(i['date'], datetime):
                self.object_ids.add(i['uniqu_id'])
                doc = Document()
                
                doc.project = project
                doc.user    = user

                doc.date    = i['date']
                doc.uniqu_id= i['uniqu_id']
                doc.title   = i['title']

                doc.source  = i['source']
                doc.authors = i['authors']
                doc.text    = i['text']

                doc.save()
                doc.corpus.add(corpus)

        self.data = []


def demo():
    import sys
    data = Europresse()
    try:
        pass
    except Exception as e:
        print("very usefull function", e)
    
        print(a['date'])


if __name__ == "__main__" :
    try:
        demo()
    except Exception as error:
        print(error)
