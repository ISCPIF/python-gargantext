from django.conf.urls import url

from . import main, auth
from . import projects, corpora, terms, graph


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
    url(r'^projects/(\d+)/corpora/(\d+)/?$', corpora.docs_by_titles),
    url(r'^projects/(\d+)/corpora/(\d+)/chart/?$', corpora.chart),

    # corpus by journals
    url(r'^projects/(\d+)/corpora/(\d+)/journals/?$', corpora.docs_by_journals),

    # terms table for the corpus
    url(r'^projects/(\d+)/corpora/(\d+)/terms/?$', terms.ngramtable),
    
    # graph explorer
    url(r'^projects/(\d+)/corpora/(\d+)/graph/?$', graph.explorer),

]
