from django.conf.urls import url

from . import nodes
from . import ngramlists


urlpatterns = [
    url(r'^nodes$'              , nodes.NodeListResource.as_view()),
    url(r'^nodes/(\d+)$'        , nodes.NodeResource.as_view()),

    url(r'^nodes/(\d+)/facets$', nodes.CorpusFacet.as_view()),

    # get a list of ngram_ids or ngram_infos by list_id
    #
    # url(r'^ngramlists/(\d+)$', ngramlists.List.as_view()),

    # entire combination of lists from a corpus
    # (or any combination of lists that go together :
    #   - a mainlist
    #   - an optional stoplist
    #   - an optional maplist
    #   - an optional grouplist
    # aka lexical model
    url(r'^ngramlists/family$', ngramlists.ListFamily.as_view()),
    
    url(r'^nodes/(\d+)/graph$'  , nodes.CorpusGraph.as_view()),
]
