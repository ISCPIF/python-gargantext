from gargantext.util.db import *
from gargantext.util.db_cache import *
from gargantext.constants import *

from gargantext.models.ngrams import Ngram, NodeNgram, NodeNgramNgram


def insert_ngrams(ngrams,get='terms-id'):
    '''
    insert_ngrams :: [(String, Int)] -> dict[terms] = id
    '''
    db, cursor = get_cursor()
    
    cursor.execute('''    
        CREATE TEMPORARY TABLE tmp__ngram (
            id INT,
            terms VARCHAR(255) NOT NULL,
            n INT
            );
        ''')

    bulk_insert('tmp__ngram', ['terms', 'n'], ngrams, cursor=cursor)
    
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
            %s (terms, n)
        SELECT
            terms, n
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
            ngram.n = tmp__ngram.n
        AND
            tmp__ngram.id IS NULL
            ''' % (Ngram.__table__.name,))
    
    ngram_ids = dict()
    cursor.execute('SELECT id, terms FROM tmp__ngram')
    for row in cursor.fetchall():
        ngram_ids[row[1]] = row[0]

    db.commit()
    return(ngram_ids)

