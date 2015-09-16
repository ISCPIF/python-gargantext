from collections import defaultdict
from datetime import datetime
from random import random
from hashlib import md5
from time import time
from math import log

from gargantext_web.db import *

from admin.utils import DebugTime

# tfidf calculation
def compute_tfidf(corpus):
    dbg = DebugTime('Corpus #%d - tfidf' % corpus.id)
    # compute terms frequency sum
    dbg.show('calculate terms frequencies sums')
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
        ''' % (NodeNodeNgram.__table__.name, corpus.id, ))
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
