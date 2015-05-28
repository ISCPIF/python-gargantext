from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.contrib.auth.views import login

from gargantext_web import views, views_optimized

import gargantext_web.api
import scrappers.scrap_pubmed.views as pubmedscrapper


admin.autodiscover()

urlpatterns = patterns('',
    
    # Admin views
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),

    url(r'^auth/$', views.login_user),
    url(r'^auth/logout/$', views.logout_user),
    
    # Dynamic CSS
    url(r'^img/logo.svg$', views.logo),
    url(r'^css/bootstrap.css$', views.css),
    
    # User Home view
    url(r'^$', views.home_view),
    url(r'^about/', views.get_about),
    url(r'^maintenance/', views.get_maintenance),
    
    # Project Management
    url(r'^projects/$', views.projects),
    url(r'^project/(\d+)/$', views_optimized.project),
    url(r'^delete/(\d+)$', views.delete_node), # => api.node('id' = id, children = 'True', copies = False)
    
    # Corpus management
    url(r'^project/(\d+)/corpus/(\d+)/$', views.corpus),
    url(r'^project/(\d+)/corpus/(\d+)/corpus.csv$', views.corpus_csv),
    url(r'^project/(\d+)/corpus/(tests_mvc_listdocuments+)/corpus.tests_mvc_listdocuments$', views.corpus_csv),

    # Visualizations
    url(r'^project/(\d+)/corpus/(\d+)/chart$', views.chart),
    url(r'^project/(\d+)/corpus/(\d+)/explorer$', views.graph),
    url(r'^project/(\d+)/corpus/(\d+)/matrix$', views.matrix),
    
    # Data management
    url(r'^chart/corpus/(\d+)/data.csv$', views.send_csv),  # => api.node.children('type' : 'data', 'format' : 'csv')
    url(r'^corpus/(\d+)/node_link.json$', views.node_link), # => api.analysis('type': 'node_link', 'format' : 'json')
    url(r'^corpus/(\d+)/adjacency.json$', views.adjacency), # => api.analysis('type': 'adjacency', 'format' : 'json')
    
    url(r'^api/tfidf/(\d+)/(\w+)$', views_optimized.tfidf),
    # url(r'^api/tfidf/(\d+)/(\w+)$', views.tfidf),
    url(r'^api/tfidf2/(\d+)/(\w+)$', views.tfidf2),

    # Data management
    #url(r'^api$', gargantext_web.api.Root), # = ?
    url(r'^api/nodes$', gargantext_web.api.NodesList.as_view()),
    url(r'^api/nodes/(\d+)$', gargantext_web.api.Nodes.as_view()),
    url(r'^api/nodes/(\d+)/children/ngrams$', gargantext_web.api.NodesChildrenNgrams.as_view()),  # => repeated children ?
    url(r'^api/nodes/(\d+)/children/hyperdata$', gargantext_web.api.NodesChildrenMetatadata.as_view()),
    url(r'^api/nodes/(\d+)/children/queries$', gargantext_web.api.NodesChildrenQueries.as_view()),
    url(r'^api/nodes/(\d+)/children/duplicates$', gargantext_web.api.NodesChildrenDuplicates.as_view()),
    # url(r'^api/nodes/(\d+)/children/duplicates/delete$', gargantext_web.api.NodesChildrenDuplicates.delete ),

    url(r'^api/nodes/(\d+)/ngrams$', gargantext_web.api.CorpusController.ngrams),

    # Provisory tests
    url(r'^ngrams$', views.ngrams),  # to be removed 
    url(r'^nodeinfo/(\d+)$', views.nodeinfo), # to be removed ?
    url(r'^tests/mvc$', views.tests_mvc),
    url(r'^tests/mvc-listdocuments$', views.tests_mvc_listdocuments),

    url(r'^tests/istextquery$', pubmedscrapper.getGlobalStatsISTEXT), # api/query?type=istext ?
    url(r'^tests/pubmedquery$', pubmedscrapper.getGlobalStats),
    url(r'^tests/project/(\d+)/pubmedquery/go$', pubmedscrapper.doTheQuery),
    url(r'^tests/project/(\d+)/ISTEXquery/go$', pubmedscrapper.testISTEX),
    url(r'^tests/paginator/corpus/(\d+)/$', views.newpaginatorJSON),
    url(r'^tests/move2trash/$' , views.move_to_trash_multiple ),
    url(r'^project/(\d+)/corpus/(\d+)/ngrams$', views.test_ngrams)
)


from django.conf import settings
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT,
        }),
        url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.STATIC_ROOT,
        }),
)

if settings.MAINTENANCE:
    urlpatterns = patterns('',
    url(r'^img/logo.svg$', views.logo),
    url(r'^css/bootstrap.css$', views.css),
    
    url(r'^$', views.home_view),
    url(r'^about/', views.get_about),
    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^.*', views.get_maintenance),
    )


