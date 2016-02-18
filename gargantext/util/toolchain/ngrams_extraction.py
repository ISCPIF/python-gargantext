from gargantext.util.db import *
from gargantext.models import *
from gargantext.constants import *
from gargantext.util.ngramsextractors import ngramsextractors

from collections import defaultdict


def extract_ngrams(corpus, rule='{<JJ.*>*<NN.*>+<JJ.*>*}', keys=('title', 'abstract', )):
    """Extract ngrams for every document below the given corpus.
    Default language is given by the resource type.
    The result is then inserted into database.
    Only fields indicated in `keys` are tagged.
    """
    db, cursor = get_cursor()
    nodes_ngrams_count = defaultdict(int)
    ngrams_data = set()
    # extract ngrams
    resource_type_index = corpus.resources()[0]['type']
    resource_type = RESOURCETYPES[resource_type_index]
    default_language_iso2 = resource_type['default_language']
    for document in corpus.children('DOCUMENT'):
        for key in keys:
            value = document.hyperdata.get(key, '')
            if len(value) == 0:
                continue
            # get ngrams
            language_iso2 = document.hyperdata.get('language_iso2', default_language_iso2)
            ngramsextractor = ngramsextractors[language_iso2]
            for ngram in ngramsextractor.extract(value):
                tokens = tuple(token[0] for token in ngram)
                terms = ' '.join(tokens)
                nodes_ngrams_count[(document.id, terms)] += 1
                ngrams_data.add((terms[:255], len(tokens), ))
    # integrate ngrams
    ngrams_ids = bulk_insert_ifnotexists(
        model = Ngram,
        uniquekey = 'terms',
        fields = ('terms', 'n'),
        data = ngrams_data,
        cursor = cursor,
    )
    db.commit()
    # integrate node-ngram associations
    nodes_ngrams_data = tuple(
        (node_ngram[0], ngrams_ids[node_ngram[1]], count)
        for node_ngram, count in nodes_ngrams_count.items()
    )
    bulk_insert(
        table = NodeNgram,
        fields = ('node_id', 'ngram_id', 'weight'),
        data = nodes_ngrams_data,
        cursor = cursor,
    )
    db.commit()
    # the end!
