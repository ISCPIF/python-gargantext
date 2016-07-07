<?php
header ("Content-Type:application/json"); 
//$string = getcwd();
//$string = str_replace("/php","",$string);

$string=dirname(dirname(getcwd())); // ProjectExplorer folder name: /var/www/ademe

//$files = getDirectoryList($string."/data");
include("DirectoryScanner.php");
$projectFolderPat = dirname(dirname(getcwd())) . "/";
$instance = new scanTree($projectFolderPat);
$instance->getDirectoryTree("data");
$gexfs=$instance->gexf_folder;
$files=array();
foreach($gexfs as $key => $value){
    array_push($files,$key);
}
$filesSorted=array();
foreach($files as $file){
    array_push($filesSorted,$file);
}
sort($filesSorted);

echo json_encode($filesSorted);

function getDirectoryList ($directory)  {
    $results = array();
    $handler = opendir($directory);
    while ($file = readdir($handler)) {
      if ($file != "." && $file != ".." && 
         (strpos($file,'.gexf~'))==false && 
         (strpos($file,'.gexf'))==true) {
        $results[] = $file;
      }
    }
    closedir($handler);
    return $results;
}

?>

