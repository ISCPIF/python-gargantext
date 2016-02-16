from celery import shared_task
from time import sleep


@shared_task
def _parse(corpus_id):
    print('ABOUT TO PARSE CORPUS #%d' % corpus_id)
    sleep(2)
    print('PARSED CORPUS #%d' % corpus_id)


def parse(corpus):
    print('ABOUT TO PLAN PARSING')
    _parse.apply_async((corpus.id,),)
    print('PLANNED PARSING')
