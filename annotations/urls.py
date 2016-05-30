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
    #    ngrams from {lists ∩ document}
    url(r'^corpora/(?P<corpus_id>[0-9]+)/documents/(?P<doc_id>[0-9]+)$', views.NgramList.as_view()), # the list associated with an ngram

    # 2016-03-24: refactoring, deactivated NgramEdit and NgramCreate
    # 2016-05-27: removed NgramEdit: replaced the local httpservice by api/ngramlists
    # url(r'^lists/(?P<list_id>[0-9]+)/ngrams/create$', views.NgramCreate.as_view()), #
]
