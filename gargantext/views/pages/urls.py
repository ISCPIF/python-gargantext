from django.conf.urls import url

from . import main, auth
from . import projects, corpora


urlpatterns = [

    # presentation pages
    url(r'^$', main.home),
    url(r'^about/?$', main.about),
    # maintenance mode
    url(r'^maintenance/?$', main.maintenance),
    # authentication
    url(r'^auth/login/?$', auth.login),
    url(r'^auth/logout/?$', auth.logout),

    # projects
    url(r'^projects/?$', projects.overview),
    url(r'^projects/(\d+)/?$', projects.project),

    # corpora
    url(r'^projects/(\d+)/corpora/(\d+)/?$', corpora.corpus),
    url(r'^projects/(\d+)/corpora/(\d+)/chart/?$', corpora.chart),

]
