from gargantext.util.db import *
from gargantext.models import *
from gargantext.util.schedule import scheduled

from time import sleep


@scheduled
def parse(corpus_id):
    print('CORPUS #%d...' % (corpus_id, ))
    corpus = session.query(Node).filter(Node.id == corpus_id).first()
    sleep(2)
    if corpus is None:
        print('NO SUCH CORPUS: #%d' % corpus_id)
        return
    print('CORPUS #%d: %s' % (corpus_id, corpus, ))
