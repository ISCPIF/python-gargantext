from django.conf.urls import url

from . import nodes


urlpatterns = [
    url(r'^nodes$', nodes.NodeListResource.as_view()),
    url(r'^nodes/(\d+)$', nodes.NodeResource.as_view()),

    url(r'^nodes/(\d+)/facets$', nodes.CorpusFacet.as_view()),
]
