from django.conf.urls import url

import scrappers.pubmed as pubmed


# /!\ urls patterns here are *without* the trailing slash

urlpatterns = [ url(r'^pubmed/query$', pubmed.getGlobalStats)
              ,
              ]
