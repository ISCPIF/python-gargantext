#!/usr/bin/python3 env
"""
For initial ngram groups via stemming
 Exemple:
   - groups['copper engrav'] = {'copper engraving':3, 'coppers engraver':1...}
   - groups['post']          = {'poste':3, 'poster':5, 'postés':2...}

   TODO use groups for aggregated occurrences/coocs counts !
"""

from gargantext.models        import Node, NodeNgramNgram
from gargantext.util.db       import session
from gargantext.util.lists    import Translations
# to convert fr => french :/
from gargantext.constants      import LANGUAGES
from gargantext.util.languages import languages
from re                       import split as resplit
from collections              import defaultdict, Counter
from nltk.stem.snowball       import SnowballStemmer

def prepare_stemmers(corpus):
    """
    Returns *several* stemmers (one for each language in the corpus)
         (as a dict of stemmers with key = language_iso2)
         languages has been previously filtered by supported source languages
         and formatted
    """
    supported_stemmers_lang = [lang for lang in corpus.hyperdata["languages"]\
                                    if lang != "__unknown__" \
                                    if lang in LANGUAGES.keys()]
    stemmers = {lang:SnowballStemmer(languages[lang].name.lower())  for lang \
                    in supported_stemmers_lang}
    stemmers['__unknown__'] = SnowballStemmer("english")
    return stemmers

def compute_groups(corpus, stoplist_id = None, overwrite_id = None):
    """
    1) Use a stemmer/lemmatizer to group forms if they have same stem/lemma
    2) Create an empty GROUPLIST node (for a list of "synonym" ngrams)
    3) Save the list to DB (list node + each grouping as listnode - ngram1 - ngram2)
    """

    stop_ngrams_ids = {}
    # we will need the ngrams of the stoplist to filter
    if stoplist_id is not None:
        for id in session.query(NodeNgram.ngram_id).filter(NodeNgram.node_id == stoplist_id).all():
            stop_ngrams_ids[id[0]] = True


    # 1) compute stems/lemmas
    #    and group if same stem/lemma
    stemmers = prepare_stemmers(corpus)
    print("# STEMMERS LOADED", stemmers)
    supported_stemmers_lang = [lang for lang in corpus.hyperdata["languages"] \
                                        if lang != "__unknown__" \
                                        and  lang in LANGUAGES.keys()]
    print("#SUPPORTED STEMMERS LANGS", supported_stemmers_lang)
    # todo dict {lg => {ngrams_todo} }
    todo_ngrams_per_lg = defaultdict(set)

    # res dict { commonstem: {ngram_1:freq_1 ,ngram_2:freq_2 ,ngram_3:freq_3} }
    my_groups = defaultdict(Counter)

    # preloop per doc to sort ngrams by language
    for doc in corpus.children('DOCUMENT'):
        if doc.id not in corpus.hyperdata['skipped_docs']:
            if ('language_iso2' in doc.hyperdata) \
                    and doc.hyperdata['language_iso2'] in supported_stemmers_lang:
                lgid = doc.hyperdata['language_iso2']

            else:
                lgid = "__unknown__"
                document.status("NGRAMS_GROUPS", error="Error: unsupported language for stemming")
                document.save_hyperdata()
                #corpus.hyperdata["skipped_docs"].append(doc.id)
                #corpus.save_hyperdata()
            # doc.ngrams is an sql query (ugly but useful intermediate step)
            # FIXME: move the counting and stoplist filtering up here
            for ngram_pack in doc.ngrams.all():
                todo_ngrams_per_lg[lgid].add(ngram_pack)

    # --------------------
    # long loop per ngrams
    for (lgid,todo_ngs) in todo_ngrams_per_lg.items():
        # fun: word::str => stem::str
        stem_it = stemmers[lgid].stem

        for ng in todo_ngs:
            doc_wei = ng[0]
            ngram  = ng[1]       # Ngram obj

            # break if in STOPLIST
            if ngram.id in stop_ngrams_ids:
                next

            lexforms = [lexunit for lexunit in resplit(r'\W+',ngram.terms)]

            # STEM IT, and this term's stems will become a new grouping key...
            stemseq = " ".join([stem_it(lexfo) for lexfo in lexforms])

            # ex:
            # groups['post'] = {'poste':3, 'poster':5, 'postés':2...}
            # groups['copper engrav'] = {'copper engraving':3, 'coppers engraver':1...}
            my_groups[stemseq][ngram.id] += doc_wei

    del todo_ngrams_per_lg

    # now serializing all groups to a list of couples
    ng_couples = []
    addcouple = ng_couples.append
    for grped_ngramids in my_groups.values():
        if len(grped_ngramids) > 1:
            # first find most frequent term in the counter
            winner_id = grped_ngramids.most_common(1)[0][0]

            for ngram_id in grped_ngramids:
                if ngram_id != winner_id:
                    addcouple((winner_id, ngram_id))

    del my_groups

    # 2) the list node
    if overwrite_id:
        # overwrite pre-existing id
        the_id = overwrite_id
    # or create the new id
    else:
        the_group =  corpus.add_child(
            typename  = "GROUPLIST",
            name = "Group (src:%s)" % corpus.name[0:10]
        )

        # and save the node
        session.add(the_group)
        session.commit()
        the_id = the_group.id

    # 3) Save each grouping couple to DB thanks to Translations.save() table
    ndngng_list = Translations(
                                [(sec,prim) for (prim,sec) in ng_couples],
                                just_items=True
                   )

    # ...referring to the list node we just got
    ndngng_list.save(the_id)

    return the_id
