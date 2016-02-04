from django.conf.urls import url

from . import main, auth


urlpatterns = [
    url(r'^$', main.home),
    url(r'^about/?$', main.about),
    url(r'^auth/login/?$', auth.login),
    url(r'^auth/logout/?$', auth.logout),
]
