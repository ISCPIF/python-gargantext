"""URL Configuration of GarganText

Views are shared between these modules:
 - `api`,            for JSON and CSV interaction with data
 - `pages`,          to present HTML views to the user
 - `contents`,       for Python-generated contents
"""

from django.conf.urls                   import include, url
from django.contrib                     import admin
from django.views.generic.base          import RedirectView        as Redirect
from django.contrib.staticfiles.storage import staticfiles_storage as static

import gargantext.views.api.urls
import gargantext.views.pages.urls


urlpatterns = [ url(r'^admin/'     , admin.site.urls                                   )
              , url(r'^api/'       , include( gargantext.views.api.urls )              )
              , url(r'^'           , include( gargantext.views.pages.urls )            )
              , url(r'^favicon.ico$', Redirect.as_view( url=static.url('favicon.ico')
                                    , permanent=False), name="favicon"                 )
              ]
