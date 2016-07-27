from gargantext.util.db import *
from gargantext.models import *
from gargantext.constants import *
#from gargantext.util.ngramsextractors import ngramsextractors

from collections import defaultdict
from re          import sub

from gargantext.util.scheduling import scheduled

def _integrate_associations(nodes_ngrams_count, ngrams_data, db, cursor):
    """
    @param ngrams_data   a set like {('single word', 2), ('apple', 1),...}
    """
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


def extract_ngrams(corpus, keys=('title', 'abstract', ), do_subngrams = DEFAULT_INDEX_SUBGRAMS):
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
        resource = corpus.resources()[0]
        source = get_resource(resource["type"])
        documents_count = 0
        #load available taggers for source default langage
        tagger_bots = {lang: load_tagger(lang) for lang in source['default_languages']}
        #skipped documents that have an unsupported languages
        corpus.skipped_docs = [doc.id for doc in corpus.children('DOCUMENT') if doc.hyperdata["language_iso2"] not in source["default_languages"]]
        print(corpus.hyperdata["languages"])
        #add it to corpus.Language info
        #diff = set(corpus.hyperdata["languages"].keys()) - set(source["default_languages"]))
        #if len(diff) > 1:


        # if lang_doc in corpus.hyperdata['languages']:
        #     skipped_lg_infos = corpus.hyperdata['languages'].pop(lang_doc)
        #     corpus.hyperdata['languages']['__skipped__'][lang_doc] = skipped_lg_infos
        #     corpus.save_hyperdata()
        #     session.commit()
        # continue
        for documents_count, document in enumerate(corpus.children('DOCUMENT')):
            lang_doc = document.hyperdata['language_iso2']
            if document not in corpus.skipped_docs:
            # if document.id in corpus.skipped_docs:
            #     # get the langage of the current document
            #     # skip document
            #     print('Unsupported language: `%s` (doc #%i)' % (lang_doc, document.id))
            #     # and remember that for later processes (eg stemming)
            #     #document.hyperdata['__skipped__'] = 'ngrams_extraction'
            #     #document.save_hyperdata()
            #     #session.commit()
            #     continue
            #
            #
            # else:
                # extract ngrams on each of the considered keys
                ngramextractor = tagger_bots[lang_doc]

                for key in keys:
                    value = document.hyperdata.get(key, None)
                    if not isinstance(value, str):
                        continue
                    # get ngrams
                    for ngram in ngramsextractor.extract(value):
                        tokens = tuple(normalize_forms(token[0]) for token in ngram)

                        if do_subngrams:
                            # ex tokens = ["very", "cool", "exemple"]
                            #    subterms = [['very', 'cool'],
                            #                ['very', 'cool', 'exemple'],
                            #                ['cool', 'exemple']]

                            subterms = subsequences(tokens)
                        else:
                            subterms = [tokens]

                        for seqterm in subterms:
                            ngram = ' '.join(seqterm)
                            if len(ngram) > 1:
                                # doc <=> ngram index
                                nodes_ngrams_count[(document.id, ngram)] += 1
                                # add fields :   terms          n
                                ngrams_data.add((ngram[:255], len(seqterm), ))

                # integrate ngrams and nodes-ngrams
                if len(nodes_ngrams_count) >= BATCH_NGRAMSEXTRACTION_SIZE:
                    _integrate_associations(nodes_ngrams_count, ngrams_data, db, cursor)
                    nodes_ngrams_count.clear()
                    ngrams_data.clear()
                if documents_count % BATCH_NGRAMSEXTRACTION_SIZE == 0:
                    corpus.status('Ngrams', progress=documents_count+1)
                    corpus.save_hyperdata()
                    session.commit()
            # integrate ngrams and nodes-ngrams
            _integrate_associations(nodes_ngrams_count, ngrams_data, db, cursor)
            corpus.status('Ngrams', progress=documents_count+1, complete=True)
            corpus.save_hyperdata()
            session.commit()
    except Exception as error:
        corpus.status('Ngrams', error=error)
        corpus.save_hyperdata()
        session.commit()
        raise error


def normalize_forms(term_str, do_lowercase=DEFAULT_ALL_LOWERCASE_FLAG):
    """
    Removes unwanted trailing punctuation
    AND optionally puts everything to lowercase

    ex /'ecosystem services'/ => /ecosystem services/

    (benefits from normalize_chars upstream so there's less cases to consider)
    """
    # print('normalize_forms  IN: "%s"' % term_str)
    term_str = sub(r'^[-\'",;/%(){}\\\[\]\. ©]+', '', term_str)
    term_str = sub(r'[-\'",;/%(){}\\\[\]\. ©]+$', '', term_str)

    if do_lowercase:
        term_str = term_str.lower()

    # print('normalize_forms OUT: "%s"' % term_str)

    return term_str


def subsequences(sequence):
    """
    For an array of length n, returns an array of subarrays
    with the original and all its sub arrays of lengths 1 to n-1

    Ex: subsequences(['Aa','Bb','Cc','Dd'])
        [
            ['Aa'],
            ['Aa', 'Bb'],
            ['Aa', 'Bb', 'Cc'],
            ['Aa', 'Bb', 'Cc', 'Dd'],
            ['Bb'],
            ['Bb', 'Cc'],
            ['Bb', 'Cc', 'Dd'],
            ['Cc'],
            ['Cc', 'Dd'],
            ['Dd']
         ]
    """
    l = len(sequence)
    li = []
    lsave = li.append
    for i in range(l):
        for j in range(i+1,l+1):
            if i != j:
                lsave(sequence[i:j])
                # debug
                # print("  >", sequence[i:j])
    return li
