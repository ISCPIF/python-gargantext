<?php
include('parameters_details.php');
  
$db= $_GET["db"];//I receive the specific database as string!
$query=$_GET["query"];
$gexf=$_GET["gexf"];

$base = new PDO("sqlite:" .$mainpath.$db);

$temp=explode('/',$db);
$project_folder=$temp[1];
$corpora=$temp[count($temp)-2];
$corporadb = new PDO("sqlite:" .$mainpath.'data/'.$corpora.'/'.$corpora.'.sqlite'); //data base with complementary data


$output = "<ul>"; // string sent to the javascript for display

#http://localhost/branch_ademe/php/test.php?type=social&query=[%22marwah,%20m%22]


$type = $_GET["type"];
$query = str_replace( '__and__', '&', $_GET["query"] );
$elems = json_decode($query);
// nombre d'item dans les tables 
$sql='SELECT COUNT(*) FROM ISIABSTRACT';
foreach ($base->query($sql) as $row) {
  $table_size=$row['COUNT(*)'];
}

///// Specific to rock //////////
// Other restrictions
// extracting the project folder and the year
if (strpos($gexf,'2013')>0){
  $year='2013'; 
  $year_filter=true;
}elseif (strpos($gexf,'2012')>0){
  $year='2012';
  $year_filter=true;
}else{
  $year_filter=false;
}

// identification d'une année pour echoing
if($project_folder=='nci'){
  $year_filter=true;  
  
}

$table = "";
$column = "";
$id="";
$twjs="tinawebJS/"; // submod path of TinaWebJS

if($type=="social"){
  $table = "ISIAUTHOR";
  $column = "data";
  $id = "id";
  $restriction='';
  $factor=10;// factor for normalisation of stars
}

if($type=="semantic"){
  $table = "ISItermsListV1";
  $column = "data";
  $id = "id";
  $restriction='';
  $factor=10;
}

// identification d'une année pour echoing
if($project_folder=='nci'){
  $restriction.=" AND ISIpubdate='2013'";
}

$sql = 'SELECT sum(tfidf),id
FROM tfidf where (';
  foreach($elems as $elem){
    $sql.=' term="'.$elem.'" OR ';
  }
#$querynotparsed=$sql;#####
  $sql = substr($sql, 0, -3);
  $sql = str_replace( ' & ', '" OR term="', $sql );

  $sql.=')'.//$restriction.
'GROUP BY '.$id.'
ORDER BY sum(tfidf) DESC
LIMIT 1000';

//echo $sql;
#$queryparsed=$sql;#####

$wos_ids = array();
$sum=0;

//echo $sql;//The final query!
// array of all relevant documents with score
$count=0;
foreach ($corporadb ->query($sql) as $row) {  
  //if ($count<4*$max_item_displayed){
    $wos_ids[$row[$id]] = $row['sum(tfidf)'];//$row["count(*)"];
    $sum = $row["count(*)"] +$sum;
  //}else{
  //  continue;
  //}
}


//arsort($wos_ids);

$number_doc=ceil(count($wos_ids)/3);
$count=0;
foreach ($wos_ids as $id => $score) { 
  if ($count<1000){
    // retrieve publication year
    $sql = 'SELECT data FROM ISIpubdate WHERE id='.$id;
    foreach ($base->query($sql) as $row) {
      $pubdate=$row['data'];
    }

    // to filter under some conditions
    $to_display=true; 
    if ($project_folder=='echoing'){
      if ($year_filter){
        if ($pubdate!=$year){
          $to_display=false;
        }
      }     
    }elseif($project_folder=='nci'){
      if ($year_filter){
        if ($pubdate!='2013'){
          $to_display=false;
        }
      } 
    }

    if ($to_display){
      $count+=1;
      $output.="<li title='".$score."'>";
      $output.=imagestar($score,$factor,$twjs).' '; 
      $sql = 'SELECT data FROM ISITITLE WHERE id='.$id;

      foreach ($base->query($sql) as $row) {
         $output.='<a href="default_doc_details.php?db='.urlencode($db).'&type='.urlencode($_GET["type"]).'&query='.urlencode($query).'&id='.$id.'">'.$row['data']." </a> ";

                        //this should be the command:
      //$output.='<a href="JavaScript:newPopup(\''.$twjs.'php/default_doc_details.php?db='.urlencode($datadb).'&id='.$id.'  \')">'.$row['data']." </a> "; 

                        //the old one:  
      //$output.='<a href="JavaScript:newPopup(\''.$twjs.'php/default_doc_details.php?id='.$id.'  \')">'.$row['data']." </a> ";   
        $external_link="<a href=http://scholar.google.com/scholar?q=".urlencode('"'.$row['data'].'"')." target=blank>".' <img width=20px src="img/gs.png"></a>'; 
        //$output.='<a href="JavaScript:newPopup(''php/doc_details.php?id='.$id.''')"> Link</a>'; 
      }

  // get the authors
      $sql = 'SELECT data FROM ISIAUTHOR WHERE id='.$id;
      foreach ($base->query($sql) as $row) {
        $output.=strtoupper($row['data']).', ';
      }

      if($project_folder!='nci'){
        
        $output.='('.$pubdate.') ';

      }else {
        $output.='(2013) ';
      }



  //<a href="JavaScript:newPopup('http://www.quackit.com/html/html_help.cfm');">Open a popup window</a>'

      $output.=$external_link."</li><br>";      
    }

  }else{
    continue;
  }
}

$output= '<h3>'.$count.' items related to: '.implode(' OR ', $elems).'</h3>'.$output;



echo $output;


function imagestar($score,$factor,$twjs) {
// produit le html des images de score
  $star_image = '';
  if ($score > .5) {
    $star_image = '';
    for ($s = 0; $s < min(5,$score/$factor); $s++) {
      $star_image.='<img src="img/star.gif" border="0" >';
    }
  } else {
    $star_image.='<img src="img/stargrey.gif" border="0">';
  }
  return $star_image;
}

?>


