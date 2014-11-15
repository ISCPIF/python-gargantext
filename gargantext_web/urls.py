from django.conf.urls import patterns, include, url

from django.contrib import admin
from django.contrib.auth.views import login

from gargantext_web.views import home, projects, project, corpus
from gargantext_web.views import delete_project, delete_corpus
from gargantext_web.views import exploration, send_csv, send_graph
from gargantext_web.views import explorer_graph, explorer_matrix, explorer_chart

import gargantext_web.api


admin.autodiscover()

urlpatterns = patterns('',
    # url(r'^$', 'gargantext_web.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    
    url(r'^$', home),
    
    url(r'^projects/$', projects),
    url(r'^project/(\d+)/delete/$', delete_project),
    
    url(r'^project/(\d+)/$', project),
    
    url(r'^project/(\d+)/corpus/(\d+)/$', corpus),
    url(r'^project/(\d+)/corpus/(\d+)/delete/$', delete_corpus),
    url(r'^project/(\d+)/corpus/(\d+)/data.csv$', send_csv),
    
    url(r'^graph$', explorer_graph),
    url(r'^chart$', explorer_chart),
    url(r'^matrix$', explorer_matrix),
    
    url(r'^exploration$', exploration),

    url(r'^chart/corpus/(\d+)/data.csv$', send_csv),
    url(r'^graph.json$', send_graph),

    url(r'^api/corpus/(\d+)/ngrams$', gargantext_web.api.ngrams),
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

