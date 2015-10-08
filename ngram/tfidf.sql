CREATE TEMPORARY TABLE tmp__tf (
ngram_id INT NOT NULL,
frequency DOUBLE PRECISION NOT NULL
);


INSERT INTO
tmp__tf (ngram_id, frequency)
SELECT
node_ngram.ngram_id AS ngram_id,
(count(*)) AS frequency
FROM node_node_ngram AS node_ngram
INNER JOIN 
node_node AS node ON node.id = node_ngram.node_id
WHERE 
node.parent_id = 241444
GROUP BY node_ngram.ngram_id;




CREATE TEMPORARY TABLE tmp__idf (
ngram_id INT NOT NULL,
idf DOUBLE PRECISION NOT NULL
);

-- TODO: unify language description of the corpus
-- if language is en, use language of doc.language_id
-- if language is fr, use language of corpus.language_id
INSERT INTO
tmp__idf(ngram_id, idf)
SELECT
node_ngram.ngram_id,
-ln(COUNT(*))
FROM
node_node_ngram AS node_ngram
INNER JOIN
tmp__tf ON tmp__tf.ngram_id = node_ngram.ngram_id
INNER JOIN
node_node as doc ON doc.id = node_ngram.node_id
--INNER JOIN
--node_node as corpus ON corpus.id = doc.parent_id
WHERE
doc.language_id = 40 AND doc.type_id = 5 -- tupe doc
--corpus.language_id = 47 AND doc.type_id = 
GROUP BY
node_ngram.ngram_id
;


SELECT count(*) from node_node as doc where doc.language_id = 40 AND doc.type_id = 5; -- tupe doc

UPDATE tmp__idf SET idf = idf + ln(235616);

SELECT * from tmp__idf ORDER BY idf; -- DESC limit 10 ;


-- total = 235616

--''' % (Node.__table__.name, Node_Ngram.__table__.name, corpus.id, ))
--cursor.execute('SELECT COUNT(*) FROM tmp__st')
--D = cursor.fetchone()[0]
--if D>0:
--lnD = log(D)


--# show off
--dbg.show('insert tfidf for %d documents' % D)
--cursor.execute('''
--INSERT INTO
--%s (nodex_id, nodey_id, ngram_id, score)
SELECT
16  AS nodex_id, -- Node with type : "Tfidf (Global)"
110 AS nodey_id, -- Node of the corpus
tf.ngram_id AS ngram_id,
(tf.frequency * idf.idf) AS score
FROM
tmp__idf AS idf
INNER JOIN
tmp__tf AS tf ON tf.ngram_id = idf.ngram_id
;


--''' % (NodeNodeNgram.__table__.name, corpus.id, ))
--
