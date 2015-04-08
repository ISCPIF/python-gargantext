

from celery import shared_task

from parsing.corpustools import add_resource, parse_resources, extract_ngrams, compute_tfidf


@shared_task
def apply_workflow(corpus):
    parse_resources(corpus)
    extract_ngrams(corpus, ['title'])
    compute_tfidf(corpus)

