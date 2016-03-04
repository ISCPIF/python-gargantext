from .parsing import parse
from .ngrams_extraction import extract_ngrams


from gargantext.util.db import session
from gargantext.models import Node

from .group import compute_groups

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

    # temporary ngram lists workflow
    group_id = compute_groups(corpus)
    print('CORPUS #%d: new grouplist = #%i' % (corpus.id, group_id))
