

ALTER TABLE ONLY node_node ALTER COLUMN date SET DEFAULT CURRENT_DATE ;

ALTER TABLE ONLY node_node ALTER COLUMN hyperdata DROP NOT NULL ;

ALTER TABLE ONLY node_node ALTER COLUMN hyperdata DROP DEFAULT ;

ALTER TABLE ONLY node_node ALTER COLUMN hyperdata TYPE JSONB USING hstore_to_json(hyperdata)::jsonb ;

ALTER TABLE ONLY node_node ALTER COLUMN hyperdata SET DEFAULT '{}'::jsonb ;

ALTER TABLE ONLY node_node ALTER COLUMN hyperdata SET NOT NULL ;

