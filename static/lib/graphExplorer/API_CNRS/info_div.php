<?php
// manage the dynamical additional information in the left panel.

// ini_set('display_errors',1);
// ini_set('display_startup_errors',1);
// error_reporting(-1);

include('parameters_details.php');

$max_item_displayed=6;
$base = new PDO("sqlite:../" .$graphdb);

include('default_div.php');


/*
 * This function gets the first db name in the data folder
 * IT'S NOT SCALABLE! (If you want to use several db's)
 */
function getDB ($directory)  {
    //$results = array();
    $result = "";
    $handler = opendir($directory);
    while ($file = readdir($handler)) {
      if ($file != "." && $file != ".." 
              && 
        ((strpos($file,'.db~'))==false && (strpos($file,'.db'))==true )
              || 
        ((strpos($file,'.sqlite~'))==false && (strpos($file,'.sqlite'))==true)
      ) {
            //$results[] = $file;
            $result = $file;
            break;
      }
    }
    closedir($handler);
    //return $results;
    return $result;
}

?>
