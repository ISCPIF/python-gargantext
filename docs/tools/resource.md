#resources

Adding a new source into Gargantext requires a previous declaration
of the source inside constants.py

```python
RESOURCETYPES= [
{    "type":9, #give a unique type int
      "name": 'SCOAP [XML]', #resource name as proposed into the add corpus FORM [generic format]
      "parser": "CernParser", #name of the new parser class inside a CERN.py file (set to None if not implemented)
      "format": 'MARC21', #specific format
      'file_formats':["zip","xml"],# accepted file format
      "crawler": "CernCrawler", #name of the new crawler class inside a CERN.py file (set to None if no Crawler implemented)
      'default_languages': ['en', 'fr'], #supported defaut languages of the source
 },
 ...
 ]
```
## adding a new parser

Once you declared your new parser inside constants.py

add your new crawler file into /srv/gargantext/utils/parsers/
following this naming convention:

* Filename must be in uppercase without the Crawler mention.
  eg. MailParser => MAIL.py
* Inside this file the Parser must be called following the exact typo declared as parser in constants.py
* Your new crawler shall inherit from baseclasse Parser and provide a parse(filebuffer) method

```python
  #!/usr/bin/python3 env
  #filename:/srv/gargantext/util/parser/MAIL.py:
  from ._Parser import Parser
  class MailParser(Parser):
      def parse(self, file):
          ...
```
## adding a new crawler

Once you declared your new parser inside constants.py
add your new crawler file into /srv/gargantext/utils/parsers/
following this naming convention:

* Filename must be in uppercase without the Crawler mention.
  eg. MailCrawler => MAIL.py
* Inside this file the Crawler must be called following the exact typo declared as crawler in constants.py
* Your new crawler shall inherit from baseclasse Crawler and provide three method:
  * scan_results => ids
  * sample = > yes/no
  * fetch

```python
  #!/usr/bin/python3 env
  #filename:/srv/gargantext/util/crawler/MAIL.py:
  from ._Crawler import Crawler
  class MailCrawler(Crawler):
      def scan_results(self, query):
        ...
        self.ids = set()
      def sample(self, results_nb):
        ...
      def fetch(self, ids):
        
```
