from admin.utils import PrintException
from gargantext_web.db import *
from parsing.corpustools import *

from gargantext_web.db import NodeNgram
from sqlalchemy import desc, asc, or_, and_, Date, cast, select
from gargantext_web.db import get_cursor, bulk_insert

def get_ngramogram(corpus, limit=None):
    """
    Ngram is a composition of ograms (ogram = 1gram)
    """
    try:
        query = (session
         .query(Ngram.id, Ngram.terms)

         .outerjoin(NgramNgram, NgramNgram.ngram_id == Ngram.id)
         .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
         .join(Node, NodeNgram.node_id == Node.id)

         .filter(Node.parent_id == corpus.id, Node.type_id == cache.NodeType['Document'].id)
         .filter(Ngram.n > 1)
         .filter(NgramNgram.id == None)

         .group_by(Ngram.id, Ngram.terms)

         )
        #print(str(query))
        if isinstance(limit, (int,)):
            query = query.limit(limit)

        return(query.all())

    except Exception as error:
        PrintException()

def split_ngram(ngram):
    if isinstance(ngram, str):

        count = 0
        result = list()
        ngram_splitted = ngram.split(' ')

        for x in ngram_splitted:
            if count <= len(ngram_splitted):
                result.append((ngram_splitted[count], count))
                count += 1
        return(result)
    else:
        print("Parameter should be a string.")

def insert_ngramngram(ngramngram):
    ngrams = list()

    for n in ngramngram:
        for i in split_ngram(n[1]):
            ngrams.append((n[0], i[0], 1, i[1]))

    db, cursor = get_cursor()

    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__ngram (
            id INT,
            ngram_id INT,
            terms VARCHAR(255) NOT NULL,
            terms_id INT,
            n INT,
            position INT
            );
        ''')

    bulk_insert('tmp__ngram', ['ngram_id', 'terms', 'n', 'position'], ngrams, cursor=cursor)

    cursor.execute('''
        UPDATE
            tmp__ngram
        SET
            terms_id = ngram.id
        FROM
            %s AS ngram
        WHERE
            tmp__ngram.terms = ngram.terms
            ''' % (Ngram.__table__.name,))

    cursor.execute('''
        INSERT INTO
            %s (n, terms)
        SELECT
            n, terms
        FROM
            tmp__ngram
        WHERE
            terms_id IS NULL
            ''' % (Ngram.__table__.name,))


    cursor.execute('''
        UPDATE
            tmp__ngram
        SET
            id = ngram.id
        FROM
            %s AS ngram
        WHERE
            ngram.terms = tmp__ngram.terms
        AND
            tmp__ngram.id IS NULL
            ''' % (Ngram.__table__.name,))

    ngram_ids = dict()
    cursor.execute('SELECT id, terms FROM tmp__ngram')
    for row in cursor.fetchall():
        ngram_ids[row[1]] = row[0]

    db.commit()
    return(ngram_ids)
    return(result)

def get_ngrams(corpus, unstemmed=True, unlemmatized=False, n=1, limit=None, count_all=False):
    '''
    Node with NodeType 'Stem' should be created at the root of the project.
    '''

    if unstemmed is True:
        node_  = session.query(Node).filter(Node.type_id == cache.NodeType['Stem'].id).first()
    try:
        query = (session
         .query(Ngram.id, Ngram.terms)
         .outerjoin(NodeNgramNgram, and_(
             NodeNgramNgram.ngramx_id == Ngram.id,
             NodeNgramNgram.node_id==node_.id)
         )

         .join(NodeNgram, NodeNgram.ngram_id == Ngram.id)
         .join(Node, NodeNgram.node_id == Node.id)

         .filter(Node.parent_id == corpus.id, Node.type_id == cache.NodeType['Document'].id)
         .filter(NodeNgramNgram.id == None)
         .filter(Ngram.n == n)

         .group_by(Ngram.id, Ngram.terms)

         )
        #print(str(query))
        if isinstance(limit, (int,)):
            query = query.limit(limit)

        if count_all is True:
            return(query.count())
        else:
            return(query.all())

    except Exception as error:
        print("Error Query:", error)

def get_stems(corpus, n=1, limit=None,
              node_stem=session.query(Node).filter(
                  Node.type_id==cache.NodeType['Stem'].id).first()):
    '''
    get_stems :: Corpus -> [Stem]
    '''
    result = set()

    if corpus.language_id is None or corpus.language_id == cache.Language['en'].id:
        from nltk.stem.porter import PorterStemmer
        stemmer = PorterStemmer()
        #stemmer.stem('honeybees')
    elif corpus.language_id == cache.Language['fr'].id:
        from nltk.stem.snowball import FrenchStemmer
        stemmer = FrenchStemmer()
        #stemmer.stem('abeilles')

    for ngram_id, word in get_ngrams(corpus, limit=limit, n=n):
        result.add((node_stem.id, ngram_id, stemmer.stem(word), n))
    return(result)

def get_lems(corpus, n=1, limit=None, node_stem=cache.Node['Lem']):
    '''
    get_stems :: Corpus -> [Lem]
    '''

    result = set()

    if corpus.language_id is None or corpus.language_id == cache.Language['en'].id:
        from nltk.wordnet import PorterStemmer
        stemmer = PorterStemmer()
        #stemmer.stem('honeybees')
    elif corpus.language_id == cache.Language['fr'].id:
        from nltk.stem.snowball import FrenchStemmer
        stemmer = FrenchStemmer()
        #stemmer.stem('abeilles')

    for ngram_id, word in get_ngrams(corpus, limit=limit, n=n):
        result.add((node_stem.id, ngram_id, stemmer.stem(word), n))
    return(result)

def insert_ngrams(stems):
    db, cursor = get_cursor()

    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__ngram (
            id INT,
            terms VARCHAR(255) NOT NULL,
            n INT
            );
        ''')

    bulk_insert('tmp__ngram', ['terms', 'n'], stems, cursor=cursor)

    cursor.execute('''
        UPDATE
            tmp__ngram
        SET
            id = ngram.id
        FROM
            %s AS ngram
        WHERE
            tmp__ngram.terms = ngram.terms
            ''' % (Ngram.__table__.name,))

    cursor.execute('''
        INSERT INTO
            %s (n, terms)
        SELECT
            n, terms
        FROM
            tmp__ngram
        WHERE
            id IS NULL
            ''' % (Ngram.__table__.name,))


    cursor.execute('''
        UPDATE
            tmp__ngram
        SET
            id = ngram.id
        FROM
            %s AS ngram
        WHERE
            ngram.terms = tmp__ngram.terms
        AND
            tmp__ngram.id IS NULL
            ''' % (Ngram.__table__.name,))

    ngram_ids = dict()
    cursor.execute('SELECT id, terms FROM tmp__ngram')
    for row in cursor.fetchall():
        ngram_ids[row[1]] = row[0]

    db.commit()
    return(ngram_ids)

def insert_nodengramstem(node_ngram_stem):
    db, cursor = get_cursor()

    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__nnn (
            id INT,
            node_id INT,
            ngramx_id INT,
            ngramy_id  INT
            );
        ''')

    bulk_insert('tmp__nnn',
                ['node_id', 'ngramx_id', 'ngramy_id'],
                node_ngram_stem, cursor=cursor)

    # nnn = NodeNgramNgram
    cursor.execute('''
        UPDATE
             tmp__nnn
        SET
            id = nnn.id
        FROM
            %s AS nnn
        WHERE
            tmp__nnn.node_id = nnn.node_id
        AND
            tmp__nnn.ngramx_id = nnn.ngramx_id
        AND
            tmp__nnn.ngramy_id = nnn.ngramy_id
            ''' % (NodeNgramNgram.__table__.name,))


    cursor.execute('''
        INSERT INTO
            %s (node_id, ngramx_id, ngramy_id, score)
        SELECT
            node_id, ngramx_id, ngramy_id, 1
        FROM
            tmp__nnn
        WHERE
            id is NULL
            ''' % (NodeNgramNgram.__table__.name,))


    db.commit()

def stem_corpus(corpus_id=None):
    '''
    Returns Int as id of the Stem Node
    stem_corpus :: Int
    '''

    corpus = session.query(Node).filter(Node.id == corpus_id).first()
    #print('Number of new ngrams to stem:',
    #      get_ngrams(corpus, n=2, count_all=True))

    if corpus is not None:
        try:
            result = get_stems(corpus, n=2)
            stems = set([(stem[2], stem[3]) for stem in result])
            #print('Number of new stems', len(stems))
            stem_ids = insert_ngrams(stems)


            node_ngram_stem = set([ (ngram[0],
                                     ngram[1],
                                     stem_ids[ngram[2]]
                                     ) for ngram in list(result) ])
            print(list(node_ngram_stem)[:3])

            insert_nodengramstem(node_ngram_stem)
        except:
            PrintException()
    else:
        print('Usage: stem_corpus(corpus_id=corpus.id)')



