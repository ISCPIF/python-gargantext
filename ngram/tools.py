from gargantext_web.db import Ngram, NodeNgram, NodeNgramNgram

from gargantext_web.db import get_cursor, bulk_insert, get_or_create_node, session,get_session

def insert_ngrams_to_list(list_of_ngrams, corpus, list_type='MapList', erase=True):
    '''
    Works only for Stop and Map
    '''
    # implicit global session

    list_node = get_or_create_node(corpus=corpus, nodetype=list_type, mysession=session)
    group_node = get_or_create_node(corpus=corpus, nodetype='GroupList', mysession=session)
    group_list = (session.query(NodeNgramNgram.ngramy_id)
                         .filter(NodeNgramNgram.id==group_node.id)
                         .all()
                 )

    #print(list_node)
    if erase == True:
        session.query(NodeNgram).filter(NodeNgram.node_id==list_node.id).delete()
        session.commit()
    
    def get_id(ngram):
        query = session.query(Ngram.id).filter(Ngram.terms==ngram).first()
        return(query)
    
    list_to_insert = list()
    
    for ngram in list_of_ngrams:
        ngram_candidate = get_id(ngram)
        if ngram_candidate is not None:
            ngram_id = ngram_candidate[0]
            if ngram_id is not None and ngram_id not in group_list:
                list_to_insert.append((list_node.id, ngram_id, 1))
    #print(list_to_insert)
    db, cursor = get_cursor()
    bulk_insert(NodeNgram, ['node_id', 'ngram_id', 'weight'], [n for n in list_to_insert])

def insert_ngrams(ngrams,get='terms-id'):
    '''
    insert_ngrams :: [String, Int] -> dict[terms] = id
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

def insert_nodengramngram(nodengramngram):
    db, cursor = get_cursor()
    
    cursor.execute('''    
        CREATE TEMPORARY TABLE tmp__nnn (
            id INT,
            node_id INT,
            ngramx_id INT,
            ngramy_id  INT
            );
        ''')

    bulk_insert('tmp__nnn', ['node_id', 'ngramx_id', 'ngramy_id'], nodengramngram, cursor=cursor)

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


