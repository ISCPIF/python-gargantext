-- CNRS Copyrights 2017
-- See Gargantext Licence for details
-- Maintainers: team@gargantext.org


-- USAGE
-- psql gargandb < occ_growth.sql

-- OCC_HIST :: Corpus.id -> GroupList.id -> MapList.id -> Start -> EndFirst -> EndLast
-- EXEMPLE USAGE 
--    SELECT * FROM OCC_HIST(182856, 183859, 183866, '1800-03-15 17:00:00+01', '2000-03-15 17:00:00+01', '2017-03-15 17:00:00+01')


-- OCC_HIST_PART :: Corpus.id -> GroupList.id -> Start -> End
DROP FUNCTION OCC_HIST_PART(integer, integer, timestamp without time zone, timestamp without time zone);
-- DROP for tests
CREATE OR REPLACE FUNCTION OCC_HIST_PART(int, int, timestamp, timestamp) RETURNS TABLE (ng_id int, score float8) 
    AS $$
-- EXPLAIN ANALYZE
    SELECT 
    COALESCE(gr.ngram1_id, ng1.ngram_id) as ng_id,
    SUM(ng1.weight) as score

    from nodes n
    
    -- BEFORE
    INNER JOIN nodes as n1 ON n1.id = n.id

    INNER JOIN nodes_ngrams ng1 ON ng1.node_id = n1.id

    -- Limit with timestamps: ]start, end]
    INNER JOIN nodes_hyperdata nh1 ON nh1.node_id = n1.id
                                  AND nh1.value_utc >  $3
                                  AND nh1.value_utc <= $4

    -- Group List
    LEFT JOIN  nodes_ngrams_ngrams gr ON ng1.ngram_id = gr.ngram2_id
                               AND gr.node_id = $2

    WHERE
        n.typename  = 4
    AND n.parent_id = $1
    GROUP BY 1
    $$
LANGUAGE SQL;

DROP FUNCTION OCC_HIST(integer, integer, integer, timestamp without time zone, timestamp without time zone, timestamp without time zone);
-- OCC_HIST :: Corpus.id -> GroupList.id -> MapList.id -> Start -> EndFirst -> EndLast
CREATE OR REPLACE FUNCTION OCC_HIST(int, int, int, timestamp, timestamp, timestamp) RETURNS TABLE (ng_id int, score numeric) 
    AS $$
    WITH OCC1 as (SELECT * from OCC_HIST_PART($1, $2, $4, $5))
       , OCC2 as (SELECT * from OCC_HIST_PART($1, $2, $5, $6))
       , GROWTH as (SELECT ml.ngram_id as ngram_id
                 , COALESCE(OCC1.score, null) as score1 
                 , COALESCE(OCC2.score, null) as score2
                    FROM nodes_ngrams ml
                        LEFT JOIN OCC1 ON OCC1.ng_id = ml.ngram_id
                        LEFT JOIN OCC2 ON OCC2.ng_id = ml.ngram_id
                    WHERE ml.node_id = $3
                    ORDER by score2 DESC)
    SELECT ngram_id, COALESCE(ROUND(CAST((100 * (score2 - score1) / COALESCE((score2 + score1), 1)) as numeric), 2), 0) from GROWTH
    $$
LANGUAGE SQL;


-- BEHAVIORAL TEST (should be equal to occ in terms table)
--    WITH OCC as (SELECT * from OCC_HIST(182856, 183859, '1800-03-15 17:00:00+01', '2300-03-15 17:00:00+01'))
--    SELECT ng_id, score from OCC 
--            INNER JOIN nodes_ngrams ml on ml.ngram_id = ng_id
--                                      AND ml.node_id = 183866
--            ORDER BY score DESC;
