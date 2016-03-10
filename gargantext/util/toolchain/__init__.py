from .parsing import parse
from .ngrams_extraction import extract_ngrams
from .hyperdata_indexing import index_hyperdata


from gargantext.util.db import session
from gargantext.models import Node


def parse_extract(corpus):
    # retrieve corpus from database from id
    if isinstance(corpus, int):
        corpus_id = corpus
        corpus = session.query(Node).filter(Node.id == corpus_id).first()
        if corpus is None:
            print('NO SUCH CORPUS: #%d' % corpus_id)
            return
    # apply actions
    print('CORPUS #%d' % (corpus.id))
    parse(corpus)
    print('CORPUS #%d: parsed' % (corpus.id))
    extract_ngrams(corpus)
    print('CORPUS #%d: extracted ngrams' % (corpus.id))

def parse_extract_indexhyperdata(corpus):
    # retrieve corpus from database from id
    if isinstance(corpus, int):
        corpus_id = corpus
        corpus = session.query(Node).filter(Node.id == corpus_id).first()
        if corpus is None:
            print('NO SUCH CORPUS: #%d' % corpus_id)
            return
    # apply actions
    print('CORPUS #%d' % (corpus.id))
    parse(corpus)
    print('CORPUS #%d: parsed' % (corpus.id))
    extract_ngrams(corpus)
    print('CORPUS #%d: extracted ngrams' % (corpus.id))
    index_hyperdata(corpus)
    print('CORPUS #%d: indexed hyperdata' % (corpus.id))
