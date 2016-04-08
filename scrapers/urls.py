from django.conf.urls import url

import scrapers.pubmed as pubmed
import scrapers.istex  as istex

#import scrapers.cern  as cern
#import scrapers.hal   as hal


# Scraping : getting data from external database
# Available databases : Pubmed, IsTex, (next: CERN)

# /!\ urls patterns here are *without* the trailing slash
urlpatterns = [ url(r'^pubmed/query$'       , pubmed.query            )
              , url(r'^pubmed/save/(\d+)' , pubmed.save              )

              , url(r'^istex/query$'        , istex.query       )
              , url(r'^istex/save/(\d+)'  , istex.save                  )

            # TODO REST API for the scrapers
            #, url(r'^rest$'              , scraping.Target.as_view()      )
              ,
              ]


#def count(keywords):
#    return 42
#
#def query_save(keywords):
#    return 'path/to/query.xml'
#
