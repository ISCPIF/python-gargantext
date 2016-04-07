from django.conf.urls import url

import scrapers.pubmed as pubmed
#import scrapers.istex  as istex

#import scrapers.cern  as cern
#import scrapers.hal   as hal


# Scraping : getting data from external database
# Available databases : Pubmed, IsTex, (next: CERN)

# /!\ urls patterns here are *without* the trailing slash
urlpatterns = [ url(r'^pubmed/query$'       , pubmed.getGlobalStats            )
              , url(r'^pubmed/search/(\d+)' , pubmed.doTheQuery                )

              , url(r'^istex/query$'        , pubmed.getGlobalStatsISTEXT       )
              , url(r'^istex/search/(\d+)'  , pubmed.testISTEX                  )
            #, url(r'^scraping$'              , scraping.Target.as_view()      )
              ,
              ]
