from django.conf.urls import patterns, url
from annotations import views


# /!\ urls patterns here are *without* the trailing slash

urlpatterns = [

    # GET [DocumentHttpService]
    # json:title,id,authors,journal,
    #      publication_date
    #      abstract_text,full_text
    url(r'^documents/(?P<doc_id>[0-9]+)$', views.Document.as_view()), # document view

    # GET [NgramListHttpService]
    #    was : lists ∩ document   (ngram_ids intersection if connected to list node_id and doc node_id)
    #    fixed 2016-01: just lists (because document doesn't get updated by POST create cf. ngram.lists.DocNgram filter commented)
    url(r'^corpora/(?P<corpus_id>[0-9]+)/documents/(?P<doc_id>[0-9]+)$', views.NgramList.as_view()), # the list associated with an ngram

    # 2016-03-24: refactoring, deactivated NgramEdit and NgramCreate
    #
    # url(r'^lists/(?P<list_id>[0-9]+)/ngrams/(?P<ngram_ids>[0-9,\+]+)+$', views.NgramEdit.as_view()),
    # POST (fixed 2015-12-16)
    # url(r'^lists/(?P<list_id>[0-9]+)/ngrams/create$', views.NgramCreate.as_view()), #
]
