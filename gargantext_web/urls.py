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
    url(r'^project/(\d+)/corpus/(\d+)/data.csv$', views.send_csv),
    
    url(r'^graph$', views.explorer_graph),
    url(r'^chart$', views.explorer_chart),
    url(r'^matrix$', views.explorer_matrix),
    
    url(r'^exploration$', views.exploration),

    url(r'^chart/corpus/(\d+)/data.csv$', views.send_csv),
    url(r'^graph.json$', views.send_graph),

    url(r'^api/nodes$', gargantext_web.api.NodesController.get),
    url(r'^api/corpus/(\d+)/ngrams$', gargantext_web.api.CorpusController.ngrams),
    url(r'^api/corpus/(\d+)/metadata$', gargantext_web.api.CorpusController.metadata),
    url(r'^api/corpus/(\d+)/data$', gargantext_web.api.CorpusController.data),

    url(r'^graph-it$', views.graph_it),
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

