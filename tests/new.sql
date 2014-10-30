INSERT INTO node_nodengramngram ( node_id, ngramX_id, ngramY_id, score)
SELECT 173 AS node_id,
       x.ngram_id AS ngramX_id,
       y.ngram_id AS ngramY_id,
       COUNT(*) AS score
FROM node_node_ngram AS x
INNER JOIN node_node_ngram AS y ON y.node_id = x.node_id

INNER JOIN node_node_ngram AS n ON 

WHERE 
x.ngram_id <> y.ngram_id

GROUP BY x.ngram_id,
         y.ngram_id HAVING score > 30 LIMIT 1000

