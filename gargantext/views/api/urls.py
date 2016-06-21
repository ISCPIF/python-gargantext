from django.conf.urls import url

from . import nodes
from . import metrics
from . import ngramlists
from . import analytics

urlpatterns = [ url(r'^nodes$'                , nodes.NodeListResource.as_view()     )
              , url(r'^nodes/(\d+)$'          , nodes.NodeResource.as_view()         )
              , url(r'^nodes/(\d+)/having$'   , nodes.NodeListHaving.as_view()       )

               # Analytics
              , url(r'^nodes/(\d+)/histories$', analytics.NodeNgramsQueries.as_view())
              , url(r'^ngrams/$'              , analytics.ApiNgrams.as_view()        )
              , url(r'hyperdata$'             , analytics.ApiHyperdata.as_view()     )
                # get a list of ngram_ids or ngram_infos by list_id
                # url(r'^ngramlists/(\d+)$', ngramlists.List.as_view()),

              , url(r'^nodes/(\d+)/facets$'   , nodes.CorpusFacet.as_view()          )
              , url(r'^nodes/(\d+)/favorites$', nodes.CorpusFavorites.as_view()      )
              # in these two routes the node is supposed to be a *corpus* node


              , url(r'^metrics/(\d+)$',         metrics.CorpusMetrics.as_view()      )
                # update all metrics for a corpus
                #  ex: PUT metrics/123
                #                     \
                #                   corpus id

              , url(r'^ngramlists/export$', ngramlists.CSVLists.as_view()            )
                # get a CSV export of the ngramlists of a corpus
                #  ex: GET ngramlists/export?corpus=43
                #  TODO : unify to a /api/ngrams?formatted=csv
                #        (similar to /api/nodes?formatted=csv)

              , url(r'^ngramlists/import$', ngramlists.CSVLists.as_view()            )
                # same handling class as export (CSVLists)
                # but this route used only for POST + file
                #                           or PATCH + other corpus id

              , url(r'^ngramlists/change$', ngramlists.ListChange.as_view()          )
                # add or remove ngram from a list
                #  ex: add <=> PUT ngramlists/change?list=42&ngrams=1,2
                #       rm <=> DEL ngramlists/change?list=42&ngrams=1,2

              ,  url(r'^ngramlists/groups$', ngramlists.GroupChange.as_view()        )
                # modify grouping couples of a group node
                #  ex: PUT/DEL ngramlists/groups?node=43
                #      & group data also in url: 767[]=209,640 & 779[]=436,265,385

              , url(r'^ngramlists/family$'     , ngramlists.ListFamily.as_view()     )
                # entire combination of lists from a corpus, dedicated to termtable
                # (or any combination of lists that go together :
                #   - a mainlist
                #   - an optional stoplist
                #   - an optional maplist
                #   - an optional grouplist

              , url(r'^ngramlists/maplist$'     , ngramlists.MapListGlance.as_view() )
                # fast access to maplist, similarly formatted for termtable
              ]
