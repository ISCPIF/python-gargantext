"""URL Configuration of GarganText

Views are shared between three main modules:
 - `api`, for JSON and CSV interaction with data
 - `pages`, to present HTML views to the user
 - `contents`, for Python-generated contents
"""

from django.conf.urls import include, url

from django.contrib import admin

import gargantext.views.api.urls
import gargantext.views.generated.urls
import gargantext.views.pages.urls


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^generated/', include(gargantext.views.generated.urls)),
    url(r'^api/', include(gargantext.views.api.urls)),
    url(r'^', include(gargantext.views.pages.urls)),
]
