from .parsing           import parse
from .ngrams_extraction import extract_ngrams
from .ngram_scores      import compute_occurrences_local, compute_tfidf_local
from .ngram_groups      import compute_groups

from gargantext.util.db import session
from gargantext.models  import Node

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

    # write occurrences to Node and NodeNodeNgram
    occnd_id = compute_occurrences_local(corpus)
    print('CORPUS #%d: new occs node #%i' % (corpus.id, occnd_id))

    # write local tfidf to Node and NodeNodeNgram
    ltfidf_id = compute_tfidf_local(corpus)
    print('CORPUS #%d: new localtfidf node #%i' % (corpus.id, ltfidf_id))

    # write groups to Node and NodeNgramNgram
    group_id = compute_groups(corpus, stoplist_id = None)
    print('CORPUS #%d: new grouplist node #%i' % (corpus.id, group_id))
