# Gargantext foundations : main definitions

Documentation valid for 3.0.\* versions of Gargantext.

## Project
A project is a list of corpora (a project may have duplicate corpora).

## Corpus
A corpus is a set of documents: duplicate documents are authorized but
not recommended for the methodology since it shows artificial repeated content in the corpus. 

Then, in the document view, users may delete duplicates with a specific
function.

## Document
A document is the main Entity of Textual Context (ETC) that is composed with:
    - a title (truncated field name in the database)
    - the date of publication
    - a journal (or source)
    - an abstract
    - the authors
Users may add many fields to the document.

The main fields mentioned above are used for the main statistics in Gargantext.


### Source Type
Source Type is the source (database) from where documents have been
extracted. 

In 3.0.\* versions of Gargantext, each corpus has only one source type
(i.e database). But user can build his own corpus with CVS format.


## Ngrams

### Definitions

### Gram 
A gram is a contiguous sequence of letters separated by spaces.

### N-gram
N-gram is a contiguous sequence of n grams separated by spaces (where n
is a non negative natural number).


## N-gram Lists


## Main ngrams lists: Stop/Map/Main

Receipe of Gargantext consist of offering the rights ngrams for the map.
A the better level of complexity in order to unveil its richness
according to this 2 main rules:

If ngrams are too specifics, then the graph becomes too sparse.
If ngrams are too generics, then the graph becomes too connected.

As a consequence, finding the right balance of specific and generic
ngrams is the main target.

In first versions of Gargantext, this balance is solved with linear
methods. After 3.1.\*, non linear methods trained on dataset of the
users enable the system to find a better balance at any scale.


### Definition

3 main kinds of lists :
    1. Stop List contains black listed ngrams i.e. the noise or in others words ngrams users do not want to deal with.
    2. Map List contains ngrams that will be shown in the map.
    3. Main list or Candidate list contains all other ngrams that are neither in the stop list or in the map list. Then it _could_ be in the map according to the choice of the user or, by default, the default parameters of Gargantext.

### Storage

Relation between the list and the ngram is stored as Node-Ngram
relation where
    - Node has type name (STOP|MAIN|MAP) and parent_id the context
      (CORPUS in version 3.0.*; but could be PROJECT)
    - Ngrams depend on the context of the Node List where NodeNgrams is
      not null and Node has typename Document.


    Node[USER](name1)
    ├── Node[PROJECT](project1)
    │   ├── Node[CORPUS](corpus1)
    │   │   ├── Node[MAPLIST](list name)
    │   │   ├── Node[STOPLIST](list name)
    │   │   ├── Node[MAINLIST](list name)
    │   │   │  
    │   │   ├── Node[DOCUMENT](doc1)
    │   │   ├── Node[DOCUMENT](doc2)
    │   │   └── Node[DOCUMENT](doc2)


### Policy

#### Algo

Let be a set of ngrams where NodeNgram != 0 then
    find 2 subsets of these ngrams that show a split 
        - stop ngrams
        - not stop ngrams
    then for the subset "not stop ngrams"
        find 2 subset of ngrams that show a split:
            - map ngrams
            - others ngrams

#### Techno algo

A classifier (Support Machine Vector) is used on the following scaled-measures
for each step:
    - Occurrences : Zip Law
    - TFICF-CORPUS-SOURCETYPE
    - TFICF-SOURCETYPE-ALL
    - Genericity score
    - Specificty score




## Metrics

### Term Frequency - Inverse Context Frequency (TF-ICF)

TFICF, short for term frequency-inverse context frequency, is a numerical
statistic that is intended to reflect how important an ngram is to a
context of text.

TFICF(ngram,contextLocal,contextGlobal) = TF(ngram,contextLocal) \* ICF(ngram, contextGlobal)
where
 * TF(ngram, contextLocal) is the ngram frequency (occurrences) in contextLocal.
 * ICF(ngram, contextGlobal) is the inverse (log) document frequency (occurrences) in contextGlobal.


Others types of TFICF:
    - TFICF(ngram, DOCUMENT, CORPUS)
    - TFICF(ngram, CORPUS, PROJECT)
    - TFICF(ngram, PROJECT, DATABASETYPE)
    - TFICF(ngram, DATABASETYPE, ALL)


If the context is a document in a set of documents (corpus), then it is a TFIDF as usual. 
Then TFICF-DOCUMENT-CORPUS == TFICF(ngram,DOCUMENT,CORPUS) = TFIDF.
TFICF is the generalization of [TFIDF, Term Frequency - Inverse Document Frequency](https://en.wikipedia.org/wiki/Tf%E2%80%93idf).



## others ngrams lists

### Group List



#### Definition
#### Policy to build group lists
#### Storage





