# Gargantext foundations 

Collaborative platform for multi-scale text experiments
Embrace the past, update the present, forecast the future.

# Main Types of Entity definitions

Documentation valid for 3.0.\* versions of Gargantext.

## Nature of the entities

In Object programming language, it is objects.
In purely functional language, it is types.


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
    - n (of the "n" gram)
    - Occurrences : Zip Law (in fact already used in TFICF, this
      features are correletad, put here for pedagogical purpose)
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

#### Implementation

TFICF = TF * log (ICF)

To prepare the groups, we need to store TF and ICF seperately (in
NodesNogram via 2 nodes).

Let be TF and ICF typename of Nodes.


    Node[USER](gargantua)
    ├── Node[OCCURRENCES](source)
    ├── Node[TF](all sourcetype)
    ├── Node[ICF](all sourcetype)
    ├── Node[SOURCETYPE](Pubmed)
    │   ├── Node[OCCURRENCES](all corpora)
    │   ├── Node[TF](all corpora)
    │   └── Node[ICF](all corpora)
    ├── Node[SOURCETYPE](WOS)




## others ngrams lists

### Group List

#### Definition

Group list gives a quantifiable link between two ngrams.


#### Policy to build group lists

To group the ngrams:
- stemming or lemming
- c-value
- clustering (see graphs)
- manually by the user (supervised learning)

The scale is the character.


#### Storage

In the table NodeNgramNgram where Node has type name Group for ngram1
and ngram2.


### Favorite List

#### Definition

Fovorite Nodes
The scale is the node.

#### Building policy

- manually by the user (supervised learning)

#### Storage

NodeNode relation where first Node has type Favorite.







