<?php
echo '<meta http-equiv="Content-type" content="text/html; charset=UTF-8"/>';
// compute the tfidf score for each terms for each document for cortext like databases and store them in a specific table
//include('parameters_details.php');
$db = new PDO("sqlite:graph.db");

$database_name='echoing.sqlite';
$project_base = new PDO("sqlite:" .$database_name);

// Table creation
// efface la base existante
$project_base->exec("DROP TABLE IF EXIST tfidf");
pt("creation of tfidf table");
//on crée un table pour les infos de clusters 
$project_base->exec("CREATE TABLE tfidf (id NUMERIC,term TEXT,tfidf NUMERIC)");

//generating number of mention of terms in the corpora
$terms_freq=array();	
pt('processing terms frequency');
$sql='SELECT count(*),data FROM ISItermsListV1 group by data';
foreach ($db->query($sql) as $term) {
	$terms_freq[$term['data']]=$term['count(*)'];	
}
pt('processing number of doc');

// nombre d'iterator_apply(iterator, function)em dans les tables 
$sql='SELECT COUNT(*) FROM ISIABSTRACT';
foreach ($db->query($sql) as $row) {
	$table_size=$row['COUNT(*)'];
}
pt($table_size.' documents in database');	
// select all the doc
$sql='SELECT * FROM ISIABSTRACT';
foreach ($db->query($sql) as $doc) {
	$id=$doc['id'];
	pt($id);
	//select all the terms of that document with their occurrences
	$sql2="SELECT count(*),data FROM ISItermsListV1 where id='".$id."' group by data";
	// for each term we compute the tfidf
	foreach ($db->query($sql2) as $term_data) {
		$term=$term_data['data'];
		$term_occ_in_doc=$term_data['count(*)'];
		$terms_tfidf=log(1+$term_occ_in_doc)*log($table_size/$terms_freq[$term]);
		$query='INSERT INTO tfidf  (id,term,tfidf) VALUES ('.$id.',"'.$term.'",'.$terms_tfidf.')';
		$project_base->query($query);		
	}
}

function pt ($string)  {
	echo $string.'<br/>';
}
?>
