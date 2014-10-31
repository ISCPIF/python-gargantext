SELECT 
177 as node_id, x.ngram_id as ngramX_id, y.ngram_id as ngramY_id, COUNT(*) AS score

FROM
node_node_ngram AS x

INNER JOIN 
node_node_ngram AS y 

ON x.node_id = y.node_id


WHERE
x.id NOT IN (SELECT id FROM node_node_ngram WHERE node_id = 174 )
AND
y.id NOT IN (SELECT id from node_node_ngram WHERE node_id = 174 )

AND
x.ngram_id <> y.ngram_id

GROUP BY
x.ngram_id, y.ngram_id

LIMIT 10
