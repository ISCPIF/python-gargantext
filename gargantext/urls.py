"""URL Configuration of GarganText

Views are shared between these modules:
 - `api`,            for JSON and CSV interaction with data
 - `pages`,          to present HTML views to the user
 - `contents`,       for Python-generated contents
 - `annotations`,    to annotate local context of a corpus (as global context)
 - `graph explorer`, to explore graphs
"""

from django.conf.urls    import include, url

from django.contrib      import admin

import gargantext.views.api.urls
import gargantext.views.generated.urls
import gargantext.views.pages.urls

# Module Annotation
    ## tempo: unchanged doc-annotations --
from annotations         import urls as annotations_urls
from annotations.views   import main as annotations_main_view

# Module "Graph Explorer"
#from graphExplorer     import urls as graphExplorer_urls
from graphExplorer.rest  import Graph
from graphExplorer.views import explorer

# Module Scrapers
from scrapers            import urls as scrapers_urls

urlpatterns = [ url(r'^admin/'     , admin.site.urls                           )
              , url(r'^api/'       , include( gargantext.views.api.urls )      )
              , url(r'^'           , include( gargantext.views.pages.urls )    )

              # Module Annotation
              # tempo: unchanged doc-annotations routes --
              , url(r'^annotations/', include( annotations_urls )              )
              , url(r'^projects/(\d+)/corpora/(\d+)/documents/(\d+)/$', annotations_main_view)

              # Module "Graph Explorer"
              , url(r'^projects/(\d+)/corpora/(\d+)/explorer$', explorer       )
              , url(r'^projects/(\d+)/corpora/(\d+)/graph$'   , Graph.as_view())
              # to be removed:
              , url(r'^projects/(\d+)/corpora/(\d+)/node_link.json$', Graph.as_view())
              #url(r'^projects/(\d+)/corpora/(\d+)/explorer$', include(graphExplorer.urls))

              # Scrapers module
              , url(r'^scrapers/'   , include( scrapers_urls )                 )
              ]
