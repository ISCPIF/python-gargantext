
-- select tous les ngrams distincts de la miam list
SELECT count(*) FROM
(
SELECT ngram_id FROM node_node_ngram 
WHERE node_id = 1380  --> node.id de la miam list
GROUP BY ngram_id
) as global
	;

-- select tous les ngrams d'un corpus ayant un stem
SELECT count(*) FROM
(
SELECT ngramx_id FROM node_nodengramngram as ng

INNER JOIN node_node_ngram as nn
ON nn.ngram_id = ng.ngramx_id

INNER JOIN node_node as n
ON n.id = nn.node_id
AND n.parent_id = 1298 --> node.id du corpus 

WHERE ng.node_id = 94  --> node.id de la stem list
GROUP BY ng.ngramx_id
) as global
	;



--- select uniquement tous les ngrams distincts qui ont des stems équivalents
-- LEFT JOIN inclusif des ngrams qui on un stem
-- LEFT JOIN exclusif des ngrams qui on un stem en commun

select count(*) from
(
SELECT ngram_id FROM node_node_ngram  as nn

INNER JOIN node_node as n
ON nn.node_id = n.id
AND n.parent_id = 1298 --> node.id du corpus 

LEFT JOIN node_nodengramngram AS nx
ON nx.node_id = 94 --> node.id Stem
AND nx.ngramx_id = nn.ngram_id 

LEFT JOIN node_nodengramngram AS ny
ON nx.ngramy_id = ny.ngramy_id 
AND nx.node_id = 94 --> node.id Stem
AND nx.ngramx_id < ny.ngramx_id  --> pour supprimer les doublons

WHERE nn.node_id = 1380 --> node.id de la miam list
-- AND ny.id is NULL

GROUP BY nn.ngram_id, nx.ngramx_id --, ny.ngramx_id
) as global
;
