<?php
$db= $_GET["db"];//I receive the specific database as string!
$terms_of_query=json_decode($_GET["query"]);
include('parameters_details.php');
$base = new PDO("sqlite:" .$mainpath.$db);
$query=$_GET["query"];
$gexf=$_GET["gexf"];
$max_tag_could_size=15;
$output = "<ul>"; // string sent to the javascript for display
$type = $_GET["type"];

$sql='SELECT id from favorites';
$wos_ids=array(); // favorite list
$num_favorite=0;
$count=0;
foreach ($base->query($sql) as $row){
        $wos_ids[$row['id']] = 1;
        $num_favorite+=1;
}

$favorite_keywords=array();

foreach ($wos_ids as $id => $score) { 
  if ($count<1000){
    // retrieve publication year
    $sql = 'SELECT data FROM ISIpubdate WHERE id='.$id;
    foreach ($base->query($sql) as $row) {
      $pubdate=$row['data'];
    }

      $count+=1;
      $output.="<li >";

      $sql = 'SELECT data FROM ISItermsListV1 WHERE id='.$id;
      foreach ($base->query($sql) as $row) {
        if (array_key_exists($row['data'], $favorite_keywords)){
          $favorite_keywords[$row['data']]=$favorite_keywords[$row['data']]+1;
        }else{
          $favorite_keywords[$row['data']]=1;
        }
      }  
      


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

// get the country
  $sql = 'SELECT data FROM ISIkeyword WHERE id='.$id;
  foreach ($base->query($sql) as $row) {
    $country=$CC[strtoupper($row['data'])];
  
    $output.=strtoupper($country).'  ';
  }


  //<a href="JavaScript:newPopup('http://www.quackit.com/html/html_help.cfm');">Open a popup window</a>'

      $output.=$external_link."</li><br>";      
    

  }else{
    continue;
  }
}



arsort($favorite_keywords);
$tag_coud_size=0;
$tag_could='';
foreach ($favorite_keywords as $key => $value) {
  if ($tag_coud_size<$max_tag_could_size){
      $tag_coud_size+=1;
      $tag_could.='<font size="'.(3+log($value)).'">'.$key.', </font>';
  }else{
    continue;
  } # code...
}


$output= '<h3>'.$num_favorite.' favorite items </h3>'.$tag_could.'<br/>'.$output;


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
