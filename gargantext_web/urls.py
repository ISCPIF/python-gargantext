from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.contrib.auth.views import login

from gargantext_web import views

import gargantext_web.api


admin.autodiscover()

urlpatterns = patterns('',
    # url(r'^$', 'gargantext_web.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    
    url(r'^$', views.home),
    
    url(r'^projects/$', views.projects),
    url(r'^project/(\d+)/delete/$', views.delete_project),
    
    url(r'^project/(\d+)/$', views.project),
    
    url(r'^project/(\d+)/corpus/(\d+)/$', views.corpus),
    url(r'^project/(\d+)/corpus/(\d+)/delete/$', views.delete_corpus),
    
    url(r'^corpus/(\d+)/explorer$', views.explorer_graph),
    url(r'^chart$', views.explorer_chart),
    url(r'^matrix$', views.explorer_matrix),
    
    #url(r'^exploration$', views.exploration),

    url(r'^chart/corpus/(\d+)/data.csv$', views.send_csv),
    url(r'^corpus/(\d+)/node_link.json$', views.node_link),
    url(r'^corpus/(\d+)/adjancy_matrix$', views.node_link),

    url(r'^api$', gargantext_web.api.Root),
    url(r'^api/nodes/(\d+)/children/metadata$', gargantext_web.api.NodesChildrenMetatadata.as_view()),
    url(r'^api/nodes/(\d+)/children/queries$', gargantext_web.api.NodesChildrenQueries.as_view()),
    
    url(r'^api/nodes$', gargantext_web.api.NodesController.get),
    url(r'^api/nodes/(\d+)/ngrams$', gargantext_web.api.CorpusController.ngrams),
    url(r'^api/nodes/(\d+)/data$', gargantext_web.api.CorpusController.data),

    url(r'^graph-it$', views.graph_it),
    url(r'^ngrams$', views.ngrams),
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

