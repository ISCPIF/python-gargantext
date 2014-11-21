SELECT
    COUNT(*) AS cooccurrences,
    ngX.terms,
    ngY.terms
FROM
    node_node AS n  -- the nodes who are direct children of the corpus
    
INNER JOIN
    node_node_ngram AS nngX ON nngX.node_id = n.id  --  list of ngrams contained in the node
INNER JOIN
    node_node_ngram AS whitelistX ON whitelistX.ngram_id = nngX.ngram_id -- list of ngrams contained in the whitelist and in the node
INNER JOIN
    node_ngram AS ngX ON ngX.id = whitelistX.ngram_id -- ngrams which are in both
    
INNER JOIN
    node_node_ngram AS nngY ON nngY.node_id = n.id
INNER JOIN
    node_node_ngram AS whitelistY ON whitelistY.ngram_id = nngY.ngram_id
INNER JOIN
    node_ngram AS ngY ON ngY.id = whitelistY.ngram_id
    
WHERE
    n.parent_id = %s
AND
    whitelistX.node_id = %s
AND
    whitelistY.node_id = %s
AND
    nngX.ngram_id < nngY.ngram_id   --  so we only get distinct pairs of ngrams
    
GROUP BY
    ngX.id,
    ngX.terms,
    ngY.id,
    ngY.terms
ORDER BY
    cooccurrences DESC
LIMIT
    200