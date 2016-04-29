#Contribution guide

## Community
* [http://gargantext.org/about](http://gargantext.org/about)
* IRC Chat: (OFTC/FreeNode) #gargantex

##Tools
* gogs
* server access
* gargantext box

##Gargantex
* Gargantex box install

(S.I.R.= Setup Install & Run procedures)

* Architecture Overview



* Database Schema Overview

* Interface design Overview

##To do:
* Docs
* Interface deisgn
* Parsers/scrapers
* Computing

## How to contribute:
    1. Clone the repo
    2. Create a new branch <username>-refactoring
    3. Run the gargantext-box
    4. Code
    5.Test
    6. Commit

### Exemple1: Adding a parser
* create your new file cern.py into gargantex/scrapers/

* reference into gargantex/scrapers/urls.py
add this line:
import scrapers.cern  as cern

* reference into gargantext/constants
```
# type 9
    {   'name': 'Cern',
        'parser': CernParser,
        'default_language': 'en',
    },
```
* add an APIKEY in gargantex/settings


### Exemple2: User Interface Design
