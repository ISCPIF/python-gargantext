"""URL Configuration of GarganText

Views are shared between these modules:
 - `contents`,       for Python-generated contents
"""

from django.conf.urls                   import include, url
from django.contrib                     import admin
from django.views.generic.base          import RedirectView        as Redirect
from django.contrib.staticfiles.storage import staticfiles_storage as static


urlpatterns = [ url(r'^admin/'     , admin.site.urls                                   )
              , url(r'^favicon.ico$', Redirect.as_view( url=static.url('favicon.ico')
                                    , permanent=False), name="favicon"                 )
              ]
