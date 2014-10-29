SELECT 
177 as node_id, x.ngram_id as ngramX_id, y.ngram_id as ngramY_id, COUNT(*) AS score

FROM
node_node_ngram AS x
INNER JOIN 
node_node_ngram AS y
ON
x.node_id = y.node_id

AND
x.ngram_id <> y.ngram_id

GROUP BY
x.ngram_id, y.ngram_id

