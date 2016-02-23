from django.conf.urls import url

from . import nodes


urlpatterns = [
    url(r'^nodes$', nodes.NodesList.as_view()),
]
