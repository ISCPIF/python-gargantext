from django.conf.urls import patterns, url

from rest_v1_0 import api, ngrams

import scrappers.scrap_pubmed.views as pubmedscrapper
import tests.ngramstable.views as samtest
import gargantext_web.views as views

urlpatterns = patterns('',
    ############################################################################
    # TODO remove function from gargantext_web.view into tests.views
    url(r'mvc$', views.tests_mvc),
    url(r'mvc-listdocuments$', views.tests_mvc_listdocuments),
    url(r'paginator/corpus/(\d+)/$', views.newpaginatorJSON),
    url(r'move2trash/$' , views.move_to_trash_multiple ),


    # TODO correct and move to scappers
    url(r'istextquery$', pubmedscrapper.getGlobalStatsISTEXT), # api/query?type=istext ?
    url(r'pubmedquery$', pubmedscrapper.getGlobalStats),
    url(r'project/(\d+)/pubmedquery/go$', pubmedscrapper.doTheQuery),
    url(r'project/(\d+)/ISTEXquery/go$', pubmedscrapper.testISTEX),

)
