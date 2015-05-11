
ALTER TABLE node_node RENAME metadata TO hyperdata ;

ALTER TABLE node_metadata RENAME TO node_hyperdata ;

ALTER TABLE node_node_metadata 
	RENAME TO node_node_hyperdata 
	RENAME metadata_id TO  hyperdata_id 
	;

