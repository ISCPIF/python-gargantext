from django.conf.urls import url

from . import nodes
from . import ngramlists

urlpatterns = [ url(r'^nodes$'                , nodes.NodeListResource.as_view())
              , url(r'^nodes/(\d+)$'          , nodes.NodeResource.as_view()    )
              , url(r'^nodes/(\d+)/facets$'   , nodes.CorpusFacet.as_view()     )
              , url(r'^nodes/(\d+)/having$'   , nodes.NodeListHaving.as_view()  )

                # get a list of ngram_ids or ngram_infos by list_id
                # url(r'^ngramlists/(\d+)$', ngramlists.List.as_view()),

              ,  url(r'^ngramlists/groups$', ngramlists.GroupChange.as_view())
                # modify grouping couples of a group node
                #  ex: POST ngramlists/groups?node=43
                #           post data looks like : {"767":[209,640],"779":[436,265,385]}"


              , url(r'^ngramlists/family$'     , ngramlists.ListFamily.as_view())
                # entire combination of lists from a corpus
                # (or any combination of lists that go together :
                #   - a mainlist
                #   - an optional stoplist
                #   - an optional maplist
                #   - an optional grouplist

              ]
