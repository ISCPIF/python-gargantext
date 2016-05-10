# ____   ____ ____  _  _   ____ _____ ____   _
#/ ___| / ___|  _ \| || | |  _ \___ /|  _ \ | |
#\___ \| |   | |_) | || |_| |_) ||_ \| |_) / __)
# ___) | |___|  _ <|__   _|  __/___) |  _ <\__ \
#|____/ \____|_| \_\  |_| |_|  |____/|_| \_(   /
#                                           |_|
#


# moissonneurs == getting data from external databases


# Available databases :
## Pubmed
## IsTex,
## TODO CERN


from django.conf.urls import url

import moissonneurs.pubmed as pubmed
import moissonneurs.istex  as istex

# TODO
#import moissonneurs.cern  as cern

# TODO
#import moissonneurs.hal         as hal
#import moissonneurs.revuesOrg   as revuesOrg


# TODO ?
# REST API for the moissonneurs

# /!\ urls patterns here are *without* the trailing slash
urlpatterns = [ url(r'^pubmed/query$'     , pubmed.query    )
              , url(r'^pubmed/save/(\d+)' , pubmed.save     )

              , url(r'^istex/query$'      , istex.query     )
              , url(r'^istex/save/(\d+)'  , istex.save      )

              # TODO
              #, url(r'^scoap3/query$'      , cern.query       )
              #, url(r'^scoap3/save/(\d+)'  , cern.save        )
              ]
