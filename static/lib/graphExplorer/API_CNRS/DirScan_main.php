<?php

header('Content-Type: application/json');

include("DirectoryScanner.php");
$projectFolderPat = dirname(dirname(getcwd())) . "/";
$instance = new scanTree($projectFolderPat);
$instance->getDirectoryTree("data");

//pr(var_dump($instance->folders));
$output = array();
$output["folders"] = $instance->folders;
$output["gexf_idfolder"] = $instance->gexf_folder;
echo json_encode($output);

// ** Debug Functions: **
function br() {
    echo "----------<br>";
}

function pr($msg) {
    echo $msg . "<br>";
}

?>
