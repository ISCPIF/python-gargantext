# ____   ____ ____  _  _   ____ _____ ____   _
#/ ___| / ___|  _ \| || | |  _ \___ /|  _ \ | |
#\___ \| |   | |_) | || |_| |_) ||_ \| |_) / __)
# ___) | |___|  _ <|__   _|  __/___) |  _ <\__ \
#|____/ \____|_| \_\  |_| |_|  |____/|_| \_(   /
#                                           |_|
#


# Scrapers == getting data from external databases


# Available databases :
## Pubmed
## IsTex,
## TODO CERN


from django.conf.urls import url

import scrapers.pubmed as pubmed
import scrapers.istex  as istex

# TODO
#import scrapers.cern  as cern

# TODO
#import scrapers.hal         as hal
#import scrapers.revuesOrg   as revuesOrg


# TODO ?
# REST API for the scrapers

# /!\ urls patterns here are *without* the trailing slash
urlpatterns = [ url(r'^pubmed/query$'     , pubmed.query    )
              , url(r'^pubmed/save/(\d+)' , pubmed.save     )

              , url(r'^istex/query$'      , istex.query     )
              , url(r'^istex/save/(\d+)'  , istex.save      )

              # TODO
              #, url(r'^cern/query$'      , cern.query       )
              #, url(r'^cern/save/(\d+)'  , cern.save        )
              ]
