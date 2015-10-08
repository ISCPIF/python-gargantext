import re
import locale
from lxml import etree
from datetime import datetime, date
from django.utils import timezone
import dateutil.parser

from .FileParser import FileParser
from ..NgramsExtractors import *

from admin.utils import PrintException

class EuropressFileParser(FileParser):

    def _parse(self, file):

        localeEncoding = "fr_FR"
        codif      = "UTF-8"
        count = 0

        if isinstance(file, str):
            file = open(file, 'rb')
        # print(file)
        contents = file.read()
        #print(len(contents))
        #return []
        encoding = self.detect_encoding(contents)
        #print(encoding)
        if encoding != "utf-8":
            try:
                contents = contents.decode("latin1", errors='replace').encode(codif)
            except:
                PrintException()
#                try:
#                    contents = contents.decode(encoding, errors='replace').encode(codif)
#                except Exception as error:
#                    print(error)

        try:
            html_parser = etree.HTMLParser(encoding=codif)
            html = etree.fromstring(contents, html_parser)

            try :

                format_europresse = 50
                html_articles = html.xpath('/html/body/table/tbody')

                if len(html_articles) < 1:
                    html_articles = html.xpath('/html/body/table')

                    if len(html_articles) < 1:
                        format_europresse = 1
                        html_articles = html.xpath('//div[@id="docContain"]')
            except :
                PrintException()

            if format_europresse == 50 :
                name_xpath      = "./tr/td/span[@class = 'DocPublicationName']"
                header_xpath    = "./tr/td/span[@class = 'DocHeader']"
                title_xpath     = "string(./tr/td/span[@class = 'TitreArticleVisu'])"
                text_xpath      = "./tr/td/descendant-or-self::*[not(self::span[@class='DocHeader'])]/text()"
            elif format_europresse == 1 :
                name_xpath      = "//span[@class = 'DocPublicationName']"
                header_xpath    = "//span[@class = 'DocHeader']"
                title_xpath     = "string(//div[@class = 'titreArticleVisu'])"
                text_xpath      = "./descendant::*[\
                        not(\
                           self::div[@class='Doc-SourceText'] \
                        or self::span[@class='DocHeader'] \
                        or self::span[@class='DocPublicationName'] \
                        or self::span[@id='docNameVisu'] \
                        or self::span[@class='DocHeader'] \
                        or self::div[@class='titreArticleVisu'] \
                        or self::span[@id='docNameContType'] \
                        or descendant-or-self::span[@id='ucPubliC_lblCertificatIssuedTo'] \
                        or descendant-or-self::span[@id='ucPubliC_lblEndDate'] \
                        or self::td[@class='txtCertificat'] \
                        )]/text()"
                doi_xpath  = "//span[@id='ucPubliC_lblNodoc']/text()"


        except Exception as error :
            PrintException()

        # parse all the articles, one by one
        try:
            for html_article in html_articles:

                hyperdata = {}

                if len(html_article):
                    for name in html_article.xpath(name_xpath):
                        if name.text is not None:
                            format_journal = re.compile('(.*), (.*)', re.UNICODE)
                            test_journal = format_journal.match(name.text)
                            if test_journal is not None:
                                hyperdata['journal'] = test_journal.group(1)
                                hyperdata['volume'] = test_journal.group(2)
                            else:
                                hyperdata['journal'] = name.text.encode(codif)

                    countbis = 0

                    for header in html_article.xpath(header_xpath):
#                        print(count)
#                        countbis += 1

#                        try:
#                            print('109', hyperdata['publication_date'])
#                        except:
#                            print('no date yet')
#                            pass

                        try:
                            text = header.text
                            #print("header", text)
                        except Exception as error:
                            print(error)


                        if isinstance(text, bytes):
                            text = text.decode(encoding)
                        format_date_fr = re.compile('\d*\s*\w+\s+\d{4}', re.UNICODE)
                        if text is not None:
                            test_date_fr = format_date_fr.match(text)
                            format_date_en = re.compile('\w+\s+\d+,\s+\d{4}', re.UNICODE)
                            test_date_en = format_date_en.match(text)
                            format_sect = re.compile('(\D+),', re.UNICODE)
                            test_sect = format_sect.match(text)
                            format_page = re.compile(', p. (\w+)', re.UNICODE)
                            test_page = format_page.match(text)
                        else:
                            test_date_fr = None
                            test_date_en = None
                            test_sect = None
                            test_page = None



                        if test_date_fr is not None:
                            self.localeEncoding = "fr_FR"
                            locale.setlocale(locale.LC_ALL, localeEncoding)
                            if encoding != "utf-8":
                                text = text.replace('י', 'é')
                                text = text.replace('ű', 'û')
                                text = text.replace(' aot ', ' août ')

                            try :
                                hyperdata['publication_date'] = datetime.strptime(text, '%d %B %Y')
                            except :
                                try:
                                    hyperdata['publication_date'] = datetime.strptime(text, '%B %Y')
                                except :
                                    try:
                                        locale.setlocale(locale.LC_ALL, "fr_FR")
                                        hyperdata['publication_date'] = datetime.strptime(text, '%d %B %Y')
                                        # hyperdata['publication_date'] = dateutil.parser.parse(text)
                                    except Exception as error:
                                        print(error, text)
                                        pass


                        if test_date_en is not None:
                            localeEncoding = "en_GB.UTF-8"
                            locale.setlocale(locale.LC_ALL, localeEncoding)
                            try :
                                hyperdata['publication_date'] = datetime.strptime(text, '%B %d, %Y')
                            except :
                                try :
                                    hyperdata['publication_date'] = datetime.strptime(text, '%B %Y')
                                except :
                                    pass

                        if test_sect is not None:
                            hyperdata['section'] = test_sect.group(1).encode(codif)

                        if test_page is not None:
                            hyperdata['page'] = test_page.group(1).encode(codif)

#                    try:
#                        print('183', hyperdata['publication_date'])
#                    except:
#                        print('no date yet')
#                        pass
#

                    hyperdata['title'] = html_article.xpath(title_xpath).encode(codif)
                    hyperdata['abstract']  = html_article.xpath(text_xpath)

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
                                hyperdata['authors'] = str.title(etree.tostring(i, method="text", encoding=codif)).encode(codif)#.split(';')
                            except:
                                hyperdata['authors'] = 'not found'
                            line = 0
                            br_tag = 10


                    try:
                        if hyperdata['publication_date'] is not None or hyperdata['publication_date'] != '':
                            try:
                                back = hyperdata['publication_date']
                            except Exception as e:
                                #print(e)
                                pass
                        else:
                            try:
                                hyperdata['publication_date'] = back
                            except Exception as e:
                                print(e)
                    except :
                        hyperdata['publication_date'] = timezone.now()

                    #if lang == 'fr':
                    #hyperdata['language_iso2'] = 'fr'
                    #elif lang == 'en':
                    #    hyperdata['language_iso2'] = 'en'


                    hyperdata['publication_year']  = hyperdata['publication_date'].strftime('%Y')
                    hyperdata['publication_month'] = hyperdata['publication_date'].strftime('%m')
                    hyperdata['publication_day']  = hyperdata['publication_date'].strftime('%d')
                    #hyperdata.pop('publication_date')

                    if len(hyperdata['abstract'])>0 and format_europresse == 50:
                        hyperdata['doi'] = str(hyperdata['abstract'][-9])
                        hyperdata['abstract'].pop()
# Here add separator for paragraphs
                        hyperdata['abstract'] = str(' '.join(hyperdata['abstract']))
                        hyperdata['abstract'] = str(re.sub('Tous droits réservés.*$', '', hyperdata['abstract']))
                    elif format_europresse == 1:
                        hyperdata['doi'] = ' '.join(html_article.xpath(doi_xpath))
                        hyperdata['abstract'] = hyperdata['abstract'][:-9]
# Here add separator for paragraphs
                        hyperdata['abstract'] = str(' '.join(hyperdata['abstract']))

                    else:
                        hyperdata['doi'] = "not found"

                    hyperdata['length_words'] = len(hyperdata['abstract'].split(' '))
                    hyperdata['length_letters'] = len(hyperdata['abstract'])

                    hyperdata['bdd']  = u'europresse'
                    hyperdata['url']  = u''

                  #hyperdata_str = {}
                    for key, value in hyperdata.items():
                        hyperdata[key] = value.decode() if isinstance(value, bytes) else value
                    yield hyperdata
                    count += 1
            file.close()

        except Exception as error:
            print(error)
            pass
