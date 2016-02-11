from django.conf.urls import url

from . import main, auth, projects


urlpatterns = [

    # presentation pages
    url(r'^$', main.home),
    url(r'^about/?$', main.about),
    # maintenance mode
    url(r'^maintenance/?$', main.maintenance),
    # authentication
    url(r'^auth/login/?$', auth.login),
    url(r'^auth/logout/?$', auth.logout),

    # overview on projects
    url(r'^projects/?$', projects.overview),
    url(r'^projects/(\d+)/?$', projects.project),

]
