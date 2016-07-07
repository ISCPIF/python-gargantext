<?php


$gexf_db = array();
$gexf_db["data/medq1/20141208_MED_01_bi.gexf"] = "data/medq1/01_medline-query1.db";

$gexf_db["data/medq2/20141128_MED_02_bi.gexf"] = "data/medq2/02_medline-query2.db";
$gexf_db["data/medq2/20141128_MED_03_bi.gexf"] = "data/medq2/02_medline-query2.db";
$gexf_db["data/medq2/20141208_MED_Author_name-ISItermsjulien_index.gexf"] = "data/medq2/02_medline-query2.db";
$gexf_db["data/20141128_GPs_03_bi.gexf"] = "data/00_grantproposals.db";
$gexf_db["data/20141215_GPs_04.gexf"] = "data/00_grantproposals.db";

# new stuff
$gexf_db["data/terrorism/terrorism_mono.gexf"] = "data/terrorism/data.db";
$gexf_db["data/terrorism/terrorism_bi.gexf"] = "data/terrorism/data.db";

# new stuff2
$gexf_db["data/ClimateChange/hnetwork-2014_2015hhn-wosclimatechange2014_2015top509-ISItermsListV3bis-ISItermsListV3bis-distributionalcooc-99999-oT0.36-20-louTrue.gexf"] = "data/ClimateChange/wosclimatechange-61715-1-wosclimatechange-db(2).db";
$gexf_db["data/ClimateChange/ClimateChangeV1.gexf"] = "data/ClimateChange/wosclimatechange-61715-1-wosclimatechange-db(2).db";
$gexf_db["data/ClimateChange/hnetwork-2014_2015hn-wosclimatechange2014_2015top509-ISItermsListV3bis-ISItermsListV3bis-distributionalcooc-99999-oT0.36-20-louTrue.gexf"] = "data/ClimateChange/wosclimatechange-61715-1-wosclimatechange-db(2).db";

$gexf= str_replace('"','',$_GET["gexf"]);

$mainpath=dirname(getcwd())."/";
$graphdb = $gexf_db[$gexf];


?>
