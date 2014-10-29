SELECT 
100 as "CoocType Node", x.ngram_id, y.ngram_id, COUNT(*) AS score

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

