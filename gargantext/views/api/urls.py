from django.conf.urls import url

from . import nodes
from . import ngramlists


urlpatterns = [
    url(r'^nodes$'              , nodes.NodeListResource.as_view()),
    url(r'^nodes/(\d+)$'        , nodes.NodeResource.as_view()),

    url(r'^nodes/(\d+)/facets$' , nodes.CorpusFacet.as_view()),
    url(r'^nodes/(\d+)/having$' , nodes.NodeListHaving.as_view()),

    # add or remove ngram from a list
    #  ex: add <=> PUT ngramlists/change?list=42&ngrams=1,2
    #       rm <=> DEL ngramlists/change?list=42&ngrams=1,2
    url(r'^ngramlists/change$', ngramlists.ListChange.as_view()),

    # get entire combination of lists from a corpus
    # (or any combination of lists that go together :
    #   - a mainlist
    #   - an optional stoplist
    #   - an optional maplist
    #   - an optional grouplist)
    url(r'^ngramlists/family$', ngramlists.ListFamily.as_view()),

]
