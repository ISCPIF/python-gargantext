from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.contrib.auth.views import login

from gargantext_web import views

import gargantext_web.api


admin.autodiscover()

urlpatterns = patterns('',
    
    # Admin views
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    
    # User views
    url(r'^$', views.home),
    
    url(r'^projects/$', views.projects),
    url(r'^project/(\d+)/delete/$', views.delete_project),
    
    url(r'^project/(\d+)/$', views.project),
    
    url(r'^project/(\d+)/corpus/(\d+)/$', views.corpus),
    url(r'^project/(\d+)/corpus/(\d+)/delete/$', views.delete_corpus),
    
    # Visualizations
    url(r'^corpus/(\d+)/explorer$', views.explorer_graph),
    url(r'^corpus/(\d+)/matrix$', views.explorer_matrix),
    
    # Getting data [which?]
    url(r'^chart/corpus/(\d+)/data.csv$', views.send_csv),
    url(r'^corpus/(\d+)/node_link.json$', views.node_link),
    url(r'^corpus/(\d+)/adjancy_matrix$', views.node_link),
    url(r'^corpus/(\d+)/adjacency.json$', views.adjacency),


    # TEST
    
    # first steps with AngularJS
    url(r'^tests/mvc$', views.tests_mvc),


    # RESTful API

    # retrieve all the metadata from a given node's children
    url(r'^api/nodes/(\d+)/children/metadata$', gargantext_web.api.NodesChildrenMetatadata.as_view()),
    # retrieve the ngrams from a given node's children
    url(r'^api/nodes/(\d+)/ngrams$', gargantext_web.api.CorpusController.ngrams),
    # perform a query on a given node's children
    url(r'^api/nodes/(\d+)/children/queries$', gargantext_web.api.NodesChildrenQueries.as_view()),
    # get all the nodes
    url(r'^api/nodes$', gargantext_web.api.NodesController.get),

    # other (DEPRECATED, TO BE REMOVED)
    url(r'^graph-it$', gargantext_web.views.graph_it),
    url(r'^api/nodes$', gargantext_web.api.NodesController.get),
    url(r'^api/corpus/(\d+)/ngrams$', gargantext_web.api.CorpusController.ngrams),
    # url(r'^api/corpus/(\d+)/metadata$', gargantext_web.api.CorpusController.metadata),
    url(r'^api/corpus/(\d+)/data$', gargantext_web.api.CorpusController.data),
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

