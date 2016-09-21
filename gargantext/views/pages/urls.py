from django.conf.urls import url

from . import main
from . import projects, corpora, terms

from .auth import LoginView, out

urlpatterns = [

    # presentation pages
    url(r'^$', main.home),
    url(r'^about/?$', main.about),
    url(r'^robots.txt$', main.robots),
    # maintenance mode
    url(r'^maintenance/?$', main.maintenance),
    # authentication
    url(r'^auth/login/?$' , LoginView.as_view()),
    url(r'^auth/logout/?$', out),

    # projects
    url(r'^projects/?$'         , projects.overview),
    url(r'^projects/(\d+)/?$'   , projects.project),

    # corpora
    url(r'^projects/(\d+)/corpora/(\d+)/?$', corpora.docs_by_titles),

    # corpus by sources
    url(r'^projects/(\d+)/corpora/(\d+)/sources/?$', corpora.docs_by_sources),
    
    # corpus by authors
    url(r'^projects/(\d+)/corpora/(\d+)/authors/?$', corpora.docs_by_authors),

    # terms table for the corpus
    url(r'^projects/(\d+)/corpora/(\d+)/terms/?$', terms.ngramtable),
    
    # Analytics
    url(r'^projects/(\d+)/corpora/(\d+)/analytics/?$', corpora.analytics),
]
