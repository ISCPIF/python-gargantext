from .parsing import parse
from .ngrams_extraction import extract_ngrams


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
    parse(corpus)
    extract_ngrams(corpus)
