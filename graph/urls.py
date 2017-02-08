from django.conf.urls import url

# Module "Graph Explorer"
from graph.rest         import Graph
from graph.views        import explorer, myGraphs
from graph.intersection import intersection


# TODO : factor urls
# url will have this pattern:
# ^explorer/$corpus_id/view
# ^explorer/$corpus_id/data.json
# ^explorer/$corpus_id/intersection

# GET ^api/projects/(\d+)/corpora/(\d+)/explorer$ -> data in json format

urlpatterns = [ url(r'^projects/(\d+)/corpora/(\d+)/explorer$'      , explorer       )
              , url(r'^projects/(\d+)/corpora/(\d+)/myGraphs$'      , myGraphs       )
              , url(r'^explorer/intersection/(\w+)$'                , intersection   )
              ]
