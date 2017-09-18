from gargantext.util.db import *
from gargantext.models import *
from gargantext.constants import *
from collections import defaultdict
from re          import sub
from gargantext.util.scheduling import scheduled

def _integrate_associations(nodes_ngrams_count, ngrams_data, db, cursor):
    """
    @param ngrams_data   a set like {('single word', 2), ('apple', 1),...}

    £TODO: load whole word dictionary in ram and check existence before inserting to db => sequential insert => probably faster!
    """
    # print('INTEGRATE', len(ngrams_data), len(nodes_ngrams_count))
    print('INTEGRATE')
    # integrate ngrams (aka new words)
    ngrams_ids = bulk_insert_ifnotexists(
        model = Ngram,                # todo type should :str ~~> :str|:re) !!!
        uniquekey = 'terms',          # todo col 'terms' should be renamed 'form' ?
        fields = ('terms', 'n'),      # todo replace by type ?
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


def extract_ngrams(corpus, keys=DEFAULT_INDEX_FIELDS, do_subngrams = DEFAULT_INDEX_SUBGRAMS):
    """Extract ngrams for every document below the given corpus.
    Default language is given by the resource type.
    The result is then inserted into database.
    Only fields indicated in `keys` are tagged.
    """
    try:
        db, cursor = get_cursor()
        nodes_ngrams_count = defaultdict(int)
        ngrams_data = set()
        #1 corpus = 1 resource
        resource = corpus.resources()[0]
        documents_count = 0
        source = get_resource(resource["type"])

        #load available taggers for default langage of plateform
        #print(LANGUAGES.keys())
        tagger_bots = {lang: load_tagger(lang) for lang in corpus.hyperdata["languages"] \
                                if lang != "__unknown__"}
        tagger_bots["__unknown__"] = load_tagger("en")
        print("#TAGGERS LOADED: ", tagger_bots)
        supported_taggers_lang = tagger_bots.keys()
        print("#SUPPORTED TAGGER LANGS", list(supported_taggers_lang))

        for documents_count, document in enumerate(corpus.children('DOCUMENT')):
            #load only the docs that have passed the parsing without error
            if document.id not in corpus.hyperdata["skipped_docs"]:

                language_iso2 = document.hyperdata.get('language_iso2', '__unknown__')

                # debug
                # print(language_iso2)

                # do we have a tagger ?
                if language_iso2 not in supported_taggers_lang:
                    #print("ERROR NO language_iso2")
                    document.status("NGRAMS", error="Error: unsupported language for tagging")
                    session.add(document)
                    session.commit()
                    corpus.hyperdata["skipped_docs"].append(document.id)
                    corpus.save_hyperdata()
                    continue

                # ready !
                tagger = tagger_bots[language_iso2]

                # to do verify if document has no KEYS to index
                # eg: use set intersect (+ loop becomes direct! with no continue)
                for key in keys:
                    try:
                        value = document.hyperdata[str(key)]
                        if not isinstance(value, str):
                            #print("DBG wrong content in doc for key", key)
                            continue
                            # get ngrams
                        for ngram in tagger.extract(value):
                            normal_forms = (normalize_forms(t[0]) for t in ngram)
                            tokens = tuple(nf for nf in normal_forms if nf)
                            if do_subngrams:
                                # ex tokens = ["very", "cool", "exemple"]
                                #    subterms = [['very', 'cool'],...]

                                subterms = subsequences(tokens)
                            else:
                                subterms = [tokens]

                            for seqterm in subterms:
                                ngram = ' '.join(seqterm)
                                nbwords = len(seqterm)
                                nbchars = len(ngram)
                                if nbchars > 1:
                                    if nbchars > 255:
                                        # max ngram length (DB constraint)
                                        ngram = ngram[:255]
                                    # doc <=> ngram index
                                    nodes_ngrams_count[(document.id, ngram)] += 1
                                    # add fields :   terms          n
                                    ngrams_data.add((ngram, nbwords, ))
                    except:
                        #value not in doc
                        continue

            # integrate ngrams and nodes-ngrams
            if len(nodes_ngrams_count) >= BATCH_NGRAMSEXTRACTION_SIZE:
                # print(len(nodes_ngrams_count),">=", BATCH_NGRAMSEXTRACTION_SIZE)
                _integrate_associations(nodes_ngrams_count, ngrams_data, db, cursor)
                nodes_ngrams_count.clear()
                ngrams_data.clear()

            # save corpus hyperdata regularly too
            if documents_count % BATCH_PARSING_SIZE == 0:
                corpus.status('Ngrams', progress=documents_count+1)
                corpus.save_hyperdata()
                session.add(corpus)
                session.commit()

        # end for doc

        # integrate remaining ngrams and nodes-ngrams (after loop)
        if len(nodes_ngrams_count) > 0:
            _integrate_associations(nodes_ngrams_count, ngrams_data, db, cursor)
            nodes_ngrams_count.clear()
            ngrams_data.clear()

        # corpus-level status => complete
        corpus.status('Ngrams', progress=documents_count+1, complete=True)
        corpus.save_hyperdata()

    # end try
    except Exception as error:
        corpus.status('Ngrams', error=error)
        corpus.save_hyperdata()
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
