from django.conf.urls import patterns, include, url

from django.contrib import admin

from gargantext_web.views import home, projects, project, corpus
from gargantext_web.views import add_corpus, add_project

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'gargantext_web.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', include(admin.site.urls)),
    url(r'^grappelli/', include('grappelli.urls')), # grappelli URLS
    
    url(r'^$', home),
    
    url(r'^projects/$', projects),
    url(r'^projects/add/$', add_project),
    
    url(r'^project/(\d+)/$', project),
    url(r'^project/(\d+)/add/$', add_corpus),
    url(r'^add/corpus/$', add_corpus), # removed soon
    
    url(r'^project/(\d+)/corpus/(\d+)/$', corpus),
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

