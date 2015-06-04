---- BASIQUE calcul des cooccurrences en ne tenant pas compte des stems équivalents
--
--	SELECT
--	-- %d as node_id,
--	ngX.id,
--	ngY.id,
--	COUNT(*) AS score
--FROM
--	node_node AS n  -- the nodes who are direct children of the corpus
--
--INNER JOIN
--	node_node_ngram AS nngX ON nngX.node_id = n.id  --  list of ngrams contained in the node
--INNER JOIN
--	node_node_ngram AS mainlistX ON mainlistX.ngram_id = nngX.ngram_id -- list of ngrams contained in the mainlist and in the node
--INNER JOIN
--	node_ngram AS ngX ON ngX.id = mainlistX.ngram_id -- ngrams which are in both
--
--INNER JOIN
--	node_node_ngram AS nngY ON nngY.node_id = n.id
--INNER JOIN
--	node_node_ngram AS mainlistY ON mainlistY.ngram_id = nngY.ngram_id
--INNER JOIN
--	node_ngram AS ngY ON ngY.id = mainlistY.ngram_id
--
--WHERE
--	n.parent_id = 1298
--AND
--	n.type_id = 5
--AND
--	mainlistX.node_id = 1382
--AND
--	mainlistY.node_id = 1382
--AND
--	nngX.ngram_id < nngY.ngram_id   --  so we only get distinct pairs of ngrams
--
--GROUP BY
--	ngX.id,
--	ngX.terms,
--	ngY.id,
--	ngY.terms
--
--ORDER BY score DESC
--LIMIT 3
--;
--

-- calcul des cooccurrences en tenant compte des stems équivalents

	SELECT
	-- %d as node_id,
	ngX.id,
	ngY.id,
	COUNT(*) AS score
FROM
	node_node AS n  -- the nodes who are direct children of the corpus

INNER JOIN
	node_node_ngram AS nngX ON nngX.node_id = n.id  --  list of ngrams contained in the node
INNER JOIN
	node_node_ngram AS mainlistX ON mainlistX.ngram_id = nngX.ngram_id -- list of ngrams contained in the mainlist and in the node
INNER JOIN
	node_ngram AS ngX ON ngX.id = mainlistX.ngram_id -- ngrams which are in both
LEFT JOIN
	node_nodengramngram AS nggXX ON nggXX.node_id = 94
	AND nggXX.ngramx_id = ngX.id
LEFT JOIN
	node_nodengramngram AS nggXY ON nggXY.node_id = 94
	AND nggXY.ngramy_id = nggXY.ngramy_id
	AND nggXY.ngramx_id < nggXY.ngramx_id

INNER JOIN
	node_node_ngram AS nngY ON nngY.node_id = n.id
INNER JOIN
	node_node_ngram AS mainlistY ON mainlistY.ngram_id = nngY.ngram_id
INNER JOIN
	node_ngram AS ngY ON ngY.id = mainlistY.ngram_id
LEFT JOIN
	node_nodengramngram AS nggYX ON nggYX.node_id = 94
	AND nggYX.ngramx_id = ngY.id
LEFT JOIN
	node_nodengramngram AS nggYY ON nggYY.node_id = 94
	AND nggYX.ngramy_id = nggYY.ngramy_id
	AND nggYX.ngramx_id < nggYY.ngramx_id

WHERE
	n.parent_id = 1298
AND
	n.type_id = 5
AND
	mainlistX.node_id = 1382
AND
	mainlistY.node_id = 1382
AND
	nngX.ngram_id < nngY.ngram_id   --  so we only get distinct pairs of ngrams
--AND
--	nggYY.id is NULL
--AND
--	nggXY.id is NULL
	
GROUP BY
	ngX.id,
	ngX.terms,
	ngY.id,
	ngY.terms

ORDER BY score DESC
LIMIT 3
;

