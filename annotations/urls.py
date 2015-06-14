from django.conf.urls import patterns, url
from annotations import views


urlpatterns = patterns('',
    url(r'^document/(?P<doc_id>[0-9]+)$', views.Document.as_view()), # document view
    url(r'^corpus/(?P<corpus_id>[0-9]+)/document/(?P<doc_id>[0-9]+)$', views.NgramList.as_view()), # the list associated with an ngram
    url(r'^lists/(?P<list_id>[0-9]+)/ngrams/(?P<ngram_id>[new0-9]+)$', views.NgramEdit.as_view()), #
)
