<?php
// manage the dynamical additional information in the left panel.
// include('parameters_details.php');

$gexf= str_replace('"','',$_GET["gexf"]);

$max_item_displayed=6;
$type = $_GET["type"];
$TITLE="ISITITLE";
$query = str_replace( '__and__', '&', $_GET["query"] );
$elems = json_decode($query);

$table = "";
$column = "";
$id="";
$twjs="API_CNRS/"; // submod path of TinaWebJS


if($type=="semantic"){
  $table = "ISItermsListV1";
  $column = "data";
  $id = "id";
  $restriction='';
  $factor=10;
}
$restriction='';
$factor=10;


$sql="";
if (count($elems)==1){// un seul mot est sélectionné, on compte les mots multiples
  $sql = 'SELECT count(*),'.$id.'
  FROM '.$table.' where (';
          foreach($elems as $elem){
                $sql.=' '.$column.'="'.$elem.'" OR ';
          }
  #$querynotparsed=$sql;#####
    $sql = substr($sql, 0, -3);
    $sql = str_replace( ' & ', '" OR '.$column.'="', $sql );
    $sql.=')'.$restriction.'
  GROUP BY '.$id.'
  ORDER BY count('.$id.') DESC
  LIMIT 1000';
}else{// on compte une seule fois un mot dans un article
  $factor=ceil(count($elems)/5); //les scores sont moins haut
  $sql='';
  foreach($elems as $elem){
            $sql.=' '.$column.'="'.$elem.'" OR ';
        }
    $sql=substr($sql, 0, -3);
    $sql='SELECT count(*),id,data FROM (SELECT *
  FROM '.$table.' where ('.$sql.')'.$restriction.'
   group by id,data) GROUP BY '.$id.'
  ORDER BY count('.$id.') DESC
  LIMIT 1000  COLLATE NOCASE';

}

// echo $sql."<br>";

$base = new PDO("sqlite:../data/terrorism/data.db");
$wos_ids = array();
$sum=0;

//The final query!
// array of all relevant documents with score

foreach ($base->query($sql) as $row) {        
        // on pondère le score par le nombre de termes mentionnés par l'article
        
        //$num_rows = $result->numRows();
        $wos_ids[$row[$id]] = $row["count(*)"];
        $sum = $row["count(*)"] +$sum;
}


// /// nombre de document associés $related
$total_count=0;
$count_max=500; 
$number_doc=count($wos_ids);
$count=0;

$all_terms_from_selected_projects=array();// list of terms for the top 6 project selected

// to filter under some conditions
$to_display=true; 
$count=0;


foreach ($wos_ids as $id => $score) { 
  if ($total_count<$count_max) {
    // retrieve publication year
    
    if ($to_display){
      $total_count+=1;

      if ($count<=$max_item_displayed){
        $count+=1;

        $sql = 'SELECT data FROM ISITITLE WHERE id='.$id.' group by data';
        foreach ($base->query($sql) as $row) {
          $external_link="<a href=http://google.com/webhp?#q=".urlencode('"'.utf8_decode($row['data']).'"')." target=blank>".' <img width=15px src="'.$twjs.'img/google.png"></a>';  
          $output.="<li title='".$score."'>";
          $output.=$external_link.imagestar($score,$factor,$twjs).' '; 
          $output.='<a href="JavaScript:newPopup(\''.$twjs.'default_doc_details2.php?gexf='.urlencode($gexf).'&query='.urlencode($query).'&type='.urlencode($_GET["type"]).'&id='.$id.' \')">'.htmlentities($row['data'], ENT_QUOTES, "UTF-8")." </a> ";
          // $output.='<a>'.htmlentities($row['data'], ENT_QUOTES, "UTF-8")." </a> ";
          
        }

        $sql = 'SELECT data FROM ISIDOI WHERE id='.$id.' group by data';
        foreach ($base->query($sql) as $row) {
          $output.=$external_link.imagestar($score,$factor,$twjs).' ';  
          $output.='<a href="JavaScript:newPopup(\''.$twjs.'default_doc_details2.php?gexf='.urlencode($gexf).'&query='.urlencode($query).'&type='.urlencode($_GET["type"]).'&id='.$id.' \')">'.htmlentities($row['data'], ENT_QUOTES, "UTF-8")." </a> ";
          
        }        // get the authors
        $sql2 = 'SELECT data FROM ISIAUTHOR WHERE id='.$id. ' group by data';
        foreach ($base->query($sql2) as $row2) {
          $output.=(str_replace("\r", "", $row2['data'])).', ';
          
        }
        $output = rtrim($output, ", ");
        $output.="</li><br>"; 

      }
    }

  } else{
    continue;
  }
}
if ($total_count<$count_max){
  $related .= $total_count;
}else{
  $related .= ">".$count_max;
}

$output .= "</ul>"; #####

// echo $output."<br>";



if($max_item_displayed>$related) $max_item_displayed=$related;
echo $news.'<br/><h4><font color="#0000FF"> Full text of top '.$max_item_displayed.'/'.$related.' related grant proposals:</font></h4>'.$output;
//pt - 301 ; 15.30


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


function imagestar($score,$factor,$twjs) {
// produit le html des images de score
  $star_image = '';
  if ($score > .5) {
    $star_image = '';
    for ($s = 0; $s < min(5,$score/$factor); $s++) {
      $star_image.='<img src="'.$twjs.'img/star.gif" border="0" >';
    }
  } else {
    $star_image.='<img src="'.$twjs.'img/stargrey.gif" border="0">';
  }
  return $star_image;
}

?>
