"""URL Configuration of GarganText

Views are shared between these modules:
 - `api`,            for JSON and CSV interaction with data
 - `pages`,          to present HTML views to the user
 - `contents`,       for Python-generated contents
 - `annotations`,    to annotate local context of a corpus (as global context)
 - `graph explorer`, to explore graphs
"""

from django.conf.urls                   import include, url
from django.contrib                     import admin
from django.views.generic.base          import RedirectView        as Redirect
from django.contrib.staticfiles.storage import staticfiles_storage as static

import gargantext.views.api.urls
import gargantext.views.pages.urls

# Module Annotation
    ## tempo: unchanged doc-annotations --
from annotations         import urls as annotations_urls
from annotations.views   import main as annotations_main_view

# Module for graph service
import graph.urls

# Module Scrapers
import moissonneurs.urls


urlpatterns = [ url(r'^admin/'     , admin.site.urls                                   )
              , url(r'^api/'       , include( gargantext.views.api.urls )              )
              , url(r'^'           , include( gargantext.views.pages.urls )            )
              , url(r'^favicon.ico$', Redirect.as_view( url=static.url('favicon.ico')
                                    , permanent=False), name="favicon"                 )

              # Module Graph
              , url(r'^'           , include( graph.urls )                             )

              # Module Annotation
              # tempo: unchanged doc-annotations routes --
              , url(r'^annotations/', include( annotations_urls )                      )
              , url(r'^projects/(\d+)/corpora/(\d+)/documents/(\d+)/(focus=[0-9,]+)?$'
                                                                , annotations_main_view)

              # Module Scrapers (Moissonneurs in French)
              , url(r'^moissonneurs/'   , include( moissonneurs.urls )                 )
              ]
