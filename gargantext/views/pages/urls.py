from django.conf.urls import url

from . import main, auth


urlpatterns = [
    # presentation pages
    url(r'^$', main.home),
    url(r'^about/?$', main.about),
    # maintenance mode
    url(r'^maintenance/?$', main.maintenance),
    # authentication
    url(r'^auth/login/?$', auth.login),
    url(r'^auth/logout/?$', auth.logout),
]
