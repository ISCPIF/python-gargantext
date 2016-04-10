from gargantext.util.db import *
from gargantext.models import *
from gargantext.constants import *
from gargantext.util.ngramsextractors import ngramsextractors

from collections import defaultdict
from re          import sub

from gargantext.util.scheduling import scheduled

def _integrate_associations(nodes_ngrams_count, ngrams_data, db, cursor):
    print('INTEGRATE')
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


def extract_ngrams(corpus, keys=('title', 'abstract', )):
    """Extract ngrams for every document below the given corpus.
    Default language is given by the resource type.
    The result is then inserted into database.
    Only fields indicated in `keys` are tagged.
    """
    try:
        db, cursor = get_cursor()
        nodes_ngrams_count = defaultdict(int)
        ngrams_data = set()
        # extract ngrams
        resource_type_index = corpus.resources()[0]['type']

        resource_type = RESOURCETYPES[resource_type_index]
        default_language_iso2 = resource_type['default_language']
        for documents_count, document in enumerate(corpus.children('DOCUMENT')):
            # get ngrams extractor for the current document
            language_iso2 = document.hyperdata.get('language_iso2', default_language_iso2)
            try:
                # this looks for a parser in constants.LANGUAGES
                ngramsextractor = ngramsextractors[language_iso2]
            except KeyError:
                # skip document
                print('Unsupported language: `%s`' % (language_iso2, ))
                # and remember that for later processes (eg stemming)
                document.hyperdata['__skipped__'] = 'ngrams_extraction'
                document.save_hyperdata()
                session.commit()
                if language_iso2 in corpus.hyperdata['languages']:
                    skipped_lg_infos = corpus.hyperdata['languages'].pop(language_iso2)
                    corpus.hyperdata['languages']['__skipped__'][language_iso2] = skipped_lg_infos
                    corpus.save_hyperdata()
                    session.commit()
                continue
            # extract ngrams on each of the considered keys
            for key in keys:
                value = document.hyperdata.get(key, None)
                if not isinstance(value, str):
                    continue
                # get ngrams
                for ngram in ngramsextractor.extract(value):
                    tokens = tuple(token[0] for token in ngram)
                    terms = normalize_terms(' '.join(tokens))
                    if len(terms) > 1:
                        nodes_ngrams_count[(document.id, terms)] += 1
                        ngrams_data.add((terms[:255], len(tokens), ))
            # integrate ngrams and nodes-ngrams
            if len(nodes_ngrams_count) >= BATCH_NGRAMSEXTRACTION_SIZE:
                _integrate_associations(nodes_ngrams_count, ngrams_data, db, cursor)
                nodes_ngrams_count.clear()
                ngrams_data.clear()
            if documents_count % BATCH_NGRAMSEXTRACTION_SIZE == 0:
                corpus.status('ngrams_extraction', progress=documents_count+1)
                corpus.save_hyperdata()
                session.commit()
        # integrate ngrams and nodes-ngrams
        _integrate_associations(nodes_ngrams_count, ngrams_data, db, cursor)
        corpus.status('ngrams_extraction', progress=documents_count+1, complete=True)
        corpus.save_hyperdata()
        session.commit()
    except Exception as error:
        corpus.status('ngrams_extraction', error=error)
        corpus.save_hyperdata()
        session.commit()
        raise error


def normalize_terms(term_str, do_lowercase=DEFAULT_ALL_LOWERCASE_FLAG):
    """
    Removes unwanted trailing punctuation
    AND optionally puts everything to lowercase

    ex /'ecosystem services'/ => /ecosystem services/

    (benefits from normalize_chars upstream so there's less cases to consider)
    """
    term_str = sub(r'^[-",;/%(){}\\\[\]\.\']+', '', term_str)
    term_str = sub(r'[-",;/%(){}\\\[\]\.\']+$', '', term_str)

    if do_lowercase:
        term_str = term_str.lower()

    return term_str
