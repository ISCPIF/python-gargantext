#from admin.env import *
from math import log
from gargantext_web.db import *
from gargantext_web.db import get_or_create_node

from admin.utils import DebugTime

def compute_tfidf(corpus):
    # compute terms frequency sum
    dbg = DebugTime('Corpus #%d - TFIDF' % corpus.id)
    dbg.show('calculate terms frequencies sums')
    tfidf_node = get_or_create_node(nodetype='Tfidf', corpus=corpus)

    db, cursor = get_cursor()
    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__st (
            node_id INT NOT NULL,
            frequency DOUBLE PRECISION NOT NULL
        )
    ''')
    cursor.execute('''
        INSERT INTO
            tmp__st (node_id, frequency)
        SELECT
            node_ngram.node_id,
            SUM(node_ngram.weight) AS frequency
        FROM
            %s AS node
        INNER JOIN
            %s AS node_ngram ON node_ngram.node_id = node.id
        WHERE
            node.parent_id = %d
        GROUP BY
            node_ngram.node_id
    ''' % (Node.__table__.name, Node_Ngram.__table__.name, corpus.id, ))
    # compute normalized terms frequencies
    dbg.show('normalize terms frequencies')
    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__tf (
            node_id INT NOT NULL,
            ngram_id INT NOT NULL,
            frequency DOUBLE PRECISION NOT NULL
        )
    ''')
    cursor.execute('''
        INSERT INTO
            tmp__tf (node_id, ngram_id, frequency)
        SELECT
            node_ngram.node_id,
            node_ngram.ngram_id,
            (node_ngram.weight / node.frequency) AS frequency
        FROM
            %s AS node_ngram
        INNER JOIN
            tmp__st AS node ON node.node_id = node_ngram.node_id
    ''' % (Node_Ngram.__table__.name, ))
    # show off
    dbg.show('compute idf')
    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__idf (
            ngram_id INT NOT NULL,
            idf DOUBLE PRECISION NOT NULL
        )
    ''')
    cursor.execute('''
        INSERT INTO
            tmp__idf(ngram_id, idf)
        SELECT
            node_ngram.ngram_id,
            -ln(COUNT(*))
        FROM
            %s AS node
        INNER JOIN
            %s AS node_ngram ON node_ngram.node_id = node.id
        WHERE
            node.parent_id = %d
        GROUP BY
            node_ngram.ngram_id
    ''' % (Node.__table__.name, Node_Ngram.__table__.name, corpus.id, ))
    cursor.execute('SELECT COUNT(*) FROM tmp__st')
    D = cursor.fetchone()[0]
    if D>0:
        lnD = log(D)
        cursor.execute('UPDATE tmp__idf SET idf = idf + %f' % (lnD, ))
        # show off
        dbg.show('insert tfidf for %d documents' % D)
        cursor.execute('''
            INSERT INTO
                %s (nodex_id, nodey_id, ngram_id, score)
            SELECT
                %d AS nodex_id,
                tf.node_id AS nodey_id,
                tf.ngram_id AS ngram_id,
                (tf.frequency * idf.idf) AS score
            FROM
                tmp__idf AS idf
            INNER JOIN
                tmp__tf AS tf ON tf.ngram_id = idf.ngram_id
        ''' % (NodeNodeNgram.__table__.name, tfidf_node.id, ))
        # # show off
        # cursor.execute('''
        #     SELECT
        #         node.name,
        #         ngram.terms,
        #         node_node_ngram.score AS tfidf
        #     FROM
        #         %s AS node_node_ngram
        #     INNER JOIN
        #         %s AS node ON node.id = node_node_ngram.nodey_id
        #     INNER JOIN
        #         %s AS ngram ON ngram.id = node_node_ngram.ngram_id
        #     WHERE
        #         node_node_ngram.nodex_id = %d
        #     ORDER BY
        #         score DESC
        # ''' % (NodeNodeNgram.__table__.name, Node.__table__.name, Ngram.__table__.name, corpus.id, ))
        # for row in cursor.fetchall():
        #     print(row)
        # the end!
        db.commit()

#http://stackoverflow.com/questions/8674718/best-way-to-select-random-rows-postgresql

def compute_tfidf_global(corpus):
    dbg = DebugTime('Corpus #%d - tfidf global' % corpus.id)
    dbg.show('calculate terms frequencies sums')

    tfidf_node = get_or_create_node(nodetype='Tfidf (global)', corpus=corpus)

    session.query(NodeNodeNgram).filter(NodeNodeNgram.nodex_id==tfidf_node.id).delete()
    session.commit()

    # compute terms frequency sum
    db, cursor = get_cursor()

    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__tf (
        ngram_id INT NOT NULL,
        frequency DOUBLE PRECISION NOT NULL
        );
    ''')

    cursor.execute('''
        INSERT INTO
        tmp__tf (ngram_id, frequency)
        SELECT
        node_ngram.ngram_id AS ngram_id,
        (count(*)) AS frequency
        FROM %s AS node_ngram
        INNER JOIN
        %s AS node ON node.id = node_ngram.node_id
        WHERE
        node.parent_id = %d
        GROUP BY node_ngram.ngram_id;
    ''' % (Node_Ngram.__table__.name, Node.__table__.name,  corpus.id, ))

    # show off
    dbg.show('compute idf')
    cursor.execute('''
        CREATE TEMPORARY TABLE tmp__idf (
            ngram_id INT NOT NULL,
            idf DOUBLE PRECISION NOT NULL
        )
    ''')

    # TODO uniform language use in corpus
    if corpus.language_id == cache.Language['fr'].id:
        lang='fr'
    else:
        lang='en'

    if lang == 'en':
        cursor.execute('''
            INSERT INTO
            tmp__idf(ngram_id, idf)
            SELECT
            node_ngram.ngram_id, -ln(COUNT(*))
            FROM
            %s AS node_ngram
            INNER JOIN
            tmp__tf ON tmp__tf.ngram_id = node_ngram.ngram_id
            INNER JOIN
            %s as doc ON doc.id = node_ngram.node_id
            INNER JOIN
            %s as corpus ON corpus.id = doc.parent_id
            WHERE
            doc.language_id = %d AND doc.type_id = %d AND corpus.type_id=%d
            -- AND RANDOM() < 0.01
            GROUP BY
            node_ngram.ngram_id
            -- limit 10000
            ;
        ''' % (Node_Ngram.__table__.name
               , Node.__table__.name
               , Node.__table__.name
               , cache.Language[lang].id
               , cache.NodeType['Document'].id
               , corpus.type_id
              )
            )

    elif lang == 'fr':
        cursor.execute('''
            INSERT INTO
            tmp__idf(ngram_id, idf)
            SELECT
            node_ngram.ngram_id, -ln(COUNT(*))
            FROM
            %s AS node_ngram
            INNER JOIN
            tmp__tf ON tmp__tf.ngram_id = node_ngram.ngram_id
            INNER JOIN
            %s as doc ON doc.id = node_ngram.node_id
            INNER JOIN
            %s as corpus ON corpus.id = doc.parent_id
            WHERE
            corpus.language_id = %d AND doc.type_id = %d AND corpus.type_id=%d
            AND RANDOM() < 0.01
            GROUP BY
            node_ngram.ngram_id
            -- limit 10000
            ;
        ''' % (Node_Ngram.__table__.name
               , Node.__table__.name
               , Node.__table__.name
               , cache.Language[lang].id
               , cache.NodeType['Document'].id
               , corpus.type_id
              )
            )


    cursor.execute('''SELECT COUNT(*) FROM %s AS doc
                   WHERE doc.language_id = %d
                   AND doc.type_id = %d
                   ''' % (Node.__table__.name, cache.Language[lang].id, cache.NodeType['Document'].id))
    D = cursor.fetchone()[0]
    if D>0:
        lnD = log(D)
        cursor.execute('UPDATE tmp__idf SET idf = idf + %f' % (lnD, ))
        # show off
        dbg.show('insert tfidf')
        cursor.execute('''
            INSERT INTO
                %s (nodex_id, nodey_id, ngram_id, score)
            SELECT
                %d AS nodex_id,
                %d AS nodey_id,
                tf.ngram_id AS ngram_id,
                (tf.frequency * idf.idf) AS score
            FROM
                tmp__idf AS idf
            INNER JOIN
                tmp__tf AS tf ON tf.ngram_id = idf.ngram_id
        ''' % (NodeNodeNgram.__table__.name, tfidf_node.id, corpus.id, ))

        db.commit()

#corpus=session.query(Node).filter(Node.id==244250).first()
#compute_tfidf_global(corpus)
