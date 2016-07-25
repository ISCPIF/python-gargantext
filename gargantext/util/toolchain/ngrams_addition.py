"""
Module for raw indexing a totally new ngram

  => creates new (doc_node <-> new_ngram) relations in NodeNgram

use cases:
  - from annotation view user selects a free segment of text to make a new ngram
  - at list import, any new list can contain ngrams that've never been extracted

prerequisite:
  - normalize_chars(new_ngram_str)
  - normalize_form(new_ngram_str)
  - add the new ngram to `ngrams` table

procedure:
  - simple regexp search of the ngram string => addition to NodeNgram
  /!\ -> morphological variants are NOT considered (ex plural or declined forms)
"""

from gargantext.models   import Ngram, Node, NodeNgram
from gargantext.util.db  import session, bulk_insert
from sqlalchemy          import distinct
from re                  import findall, IGNORECASE

# TODO from gargantext.constants import LIST_OF_KEYS_TO_INDEX = title, abstract

def index_new_ngrams(ngram_ids, corpus, keys=('title', 'abstract', )):
    """
    Find occurrences of some ngrams for every document of the given corpus.
    + insert them in the NodeNgram table.

    @param ngram_ids: a list of ids for Ngram objects
                      (we assume they already went throught normalizations
                       and they were already added to Ngrams table
                       and optionally to some of the lists like MAPLIST)

            (but we can't know if they were previously indexed in the corpus)

    @param corpus: the CORPUS node

    @param keys: the hyperdata fields to index
    """

    # check the ngrams we won't process (those that were already indexed)
    indexed_ngrams_subquery = (session
                                .query(distinct(NodeNgram.ngram_id))
                                .join(Node, Node.id == NodeNgram.node_id)
                                .filter(Node.parent_id == corpus.id)
                                .filter(Node.typename == 'DOCUMENT')
                                .subquery()
                                )

    # retrieve the ngrams from our list, filtering out the already indexed ones
    todo_ngrams = (session
                    .query(Ngram)
                    .filter(Ngram.id.in_(ngram_ids))
                    .filter(~ Ngram.id.in_(indexed_ngrams_subquery))
                    .all()
                    )

    # initialize result dict
    node_ngram_to_write = {}

    # loop throught the docs and their text fields
    for doc in corpus.children('DOCUMENT'):

        # a new empty counting subdict
        node_ngram_to_write[doc.id] = {}

        for key in keys:
            # a text field
            text = doc.hyperdata.get(key, None)

            if not isinstance(text, str):
                # print("WARN: doc %i has no text in field %s" % (doc.id, key))
                continue

            for ngram in todo_ngrams:
                # build regexp : "british" => r'\bbritish\b'
                ngram_re = r'\b%s\b' % ngram.terms

                # --------------------------------------- find ---
                n_occs = len(findall(ngram_re, text, IGNORECASE))
                # -----------------------------------------------

                # save the count results
                if n_occs > 0:
                    if ngram.id not in node_ngram_to_write[doc.id]:
                        node_ngram_to_write[doc.id][ngram.id] = n_occs
                    else:
                        node_ngram_to_write[doc.id][ngram.id] += n_occs

    # integrate all at the end
    my_new_rows = []
    add_new_row = my_new_rows.append
    for doc_id in node_ngram_to_write:
        for ngram_id in node_ngram_to_write[doc_id]:
            wei = node_ngram_to_write[doc_id][ngram_id]
            add_new_row([doc_id, ngram_id, wei])

    del node_ngram_to_write

    bulk_insert(
        table = NodeNgram,
        fields = ('node_id', 'ngram_id', 'weight'),
        data = my_new_rows
    )

    n_added = len(my_new_rows)
    print("index_new_ngrams: added %i new NodeNgram rows" % n_added)

    return n_added
