from django.conf.urls import patterns, url

from gargantext_web import views_optimized

from rest_v1_0 import api, ngrams, graph

from annotations import views

urlpatterns = patterns('',
    # REST URLS
    # What is REST ?
    # https://en.wikipedia.org/wiki/Representational_state_transfer
    
    #url(r'^api$', rest_v1_0.api.Root), # = ?
    url(r'nodes$', api.NodesList.as_view()),
    url(r'nodes/(\d+)$', api.Nodes.as_view()),
    url(r'nodes/(\d+)/children/ngrams$', api.NodesChildrenNgrams.as_view()),  # => repeated children ?

    # NGRAMS table & annotations
    url(r'node/(\d+)/ngrams$'      , ngrams.Ngrams.as_view()),
    url(r'node/(\d+)/ngrams/group$', ngrams.Group.as_view()),
    url(r'node/(\d+)/ngrams/keep$', ngrams.Keep.as_view()),
    # url(r'node/(?P<list_id>[0-9]+)/ngrams/keep/(?P<ngram_ids>[0-9,\+]+)+$' , ngrams.Keep.as_view()),
    url(r'node/(?P<list_id>[0-9]+)/ngrams/(?P<ngram_ids>[0-9,\+]+)+$', views.NgramEdit.as_view()),
    url(r'node/(?P<corpus_id>[0-9]+)/ngrams/list/(?P<list_name>\w+)$' , ngrams.List.as_view()),

    #url(r'nodes/(\d+)/children/hyperdata$', api.NodesChildrenMetatadata.as_view()),
    #url(r'nodes/(\d+)/children/hyperdata$', api.NodesChildrenMetatadata.as_view()),

    url(r'nodes/(\d+)/children/queries$', api.NodesChildrenQueries.as_view()),
    url(r'nodes/(\d+)/children/duplicates$', api.NodesChildrenDuplicates.as_view()),
    # url(r'^api/nodes/(\d+)/children/duplicates/delete$', api.NodesChildrenDuplicates.delete ),
    url(r'nodes/(\d+)/ngrams$', api.CorpusController.ngrams),
    
    url(r'nodes/(\d+)/graph$', graph.Graph.as_view()),
    url(r'corpus/(\d+)/graph$', graph.Graph.as_view()),
    
    url(r'hyperdata$', api.ApiHyperdata.as_view()),
    url(r'ngrams$', api.ApiNgrams.as_view()),
    
    url(r'tfidf/(\d+)/(\w+)$', views_optimized.tfidf),
)

