//Function that creates contextual help button

help = { "#project":{
            "en":
              { "title":"Adding a project",
                "content": "Click on the button and give a name to your projet",
              },
            "fr":
              { "title": "Pour ajouter un projet",
                "content":"Cliquez sur le bouton et donnez un nom à votre projet",
              },
              "placement":"bottom",
              "position": "inside",
          },
          "#corpus":{
            "en":
              { "title":"Adding a corpus",
              "content": "<p>To add a corpus to your project"+
                        "<br><b>Select a database</b></br>"+
                        "<b><span class='glyphicon glyphicon-hand-right'></span>  If you have a file to upload already :</b>"+
                        "<ol>"+
                        "<li>Check your file is <a target='_blank' href='https://iscpif.fr/gargantext/import-formats_en/'>zipped (.zip archive) </a> and with the right <a href='https://iscpif.fr/gargantext/import-formats'>format</a></li>"+
                        "<li>Click on 'Chose a file...'</li>"+
                        "<li>And give a name to your corpus</li>"+
                        "<li>Click on 'Process this!'</li></ol>"+
                        "<b><span class='glyphicon glyphicon-hand-right'></span>  If you want to import a corpus from an open database <small>(only supported by PubMed, IsTex or SCOAP3 right now)</small>:</b>"+
                        "<ol>"+
                        "<li>Select No option to the question 'Do you have a file already?'</li>"+
                        "<li>Enter your query (syntax of the database is still the same)</li>"+
                        "<li>Then click on 'Scan' to discover the number of results to your query</li>"+
                        "<li>Click on 'Download!' ton import et analyze a random set of document</li>"+
                        "</ul>"+
                        "</p>",
              },
            "fr":
              { "title": "Pour ajouter un corpus",
                "content": "<p>Pour ajouter un corpus à votre projet"+
                        "<br><b>Sélectionnez une base de données</b></br>"+
                        "<b><span class='glyphicon glyphicon-hand-right'></span>   Si vous avez déjà un fichier à téléverser :</b>"+
                        "<ol>"+
                        "<li>Vérifiez que votre fichier est <a href='https://iscpif.fr/gargantext/import-formats_fr/'>compressé (archive .zip) </a> et dans le bon <a href='https://iscpif.fr/gargantext/import-formats'>format</a></li>"+
                        "<li>Cliquez sur 'Choisir un fichier...'</li>"+
                        "<li>Puis donnez un nom à votre corpus</li>"+
                        "<li>Cliquez sur 'Process this!'</li></ol>"+
                        "<b><span class='glyphicon glyphicon-hand-right'></span>  Si vous souhaitez importer un corpus directement depuis une base de donnée ouverte <small>(SCOAP3, PubMed ou IsTex pour le moment)</small>:</b>"+
                        "<ol>"+
                        "<li>Sélectionnez l'option No à la question Do you have a file already?</li>"+
                        "<li>Entrez votre requête (la syntaxe de la base de donnée cible est conservée)</li>"+
                        "<li>Cliquez ensuite sur 'Scan' pour avoir le nombre de résultats de votre requête</li>"+
                        "<li>Cliquez sur 'Download!' pour importer et analyser un échantillon prélevé de manière aléatoire</li>"+
                        "</ul>"+
                        "</p>",
                      },
            "placement": "right",
            "position": "inside",
            },

          '#docFilter':{
            "en":{
                "title":"Filter document",
                "content": "Given the option you selected in the menu all the documents, favorites or duplicates will appear"
                },
            "fr": {
              "title": "Filtrer les documents",
              "content": "En selectionnant l'option correspondante dans le menu déroulant, vous pouvez afficher ici tous les documents, uniquement vos favoris ou encore rechercher les doublons pour les supprimer",
            },
            "placement":"right",
            "position": "inside",
          },
          '#titles_time':{
            "en":{
              "title":"Filter by date",
              "content": "Select a specific period using the cursor on the above histogram."+
              "The distribution of documents and their occurrences for this period will be displayed in the lower part",
            },
            "fr":{
              "title": "Filtrer par date",
              "content": "Selectionnez une période spécifique en utilisant le curseur sur l'histogramme ci-dessus."+
              "La répartition des documents et leurs occurences pour cette période s'affichera dans la partie inférieure.",
            },
            "placement": "right",
            "position": "inside",
          },
          '#sources_time':{
            "en":{"title": "Filter sources",
                  "content":"Select a range of minimum and maximum number of source publications by using the cursor on the above histogram."+
                  "The sources for this range with the number of publications will appear in the lower part.",
            },
            "fr":{
              "title": "Filtrer par nombre de publications",
              "content": "Selectionnez une plage de nombre minimal et maximal de publications par source en utilisant le curseur sur l'histogramme ci-dessus."+
              "Les sources correspondant à cette plage temporelle avec leur nombre de publications s'affichera dans la partie inférieure.",
            },
            "placement": "right",
            "position": "inside",
          },
          '#terms_time':{
            "en":{"title":"Filter terms",
                  "content":"Select a range of occurrences by using the cursor on the histogram above."+
                            "The list of terms which the number of occurrences falls into this range will appear at the bottom.",
            },
            "fr":{
              "title": "Filtrer les termes par occurrences",
              "content": "Selectionnez une plage d'occurences en utilisant le curseur sur l'histogramme ci dessus."+
                         "La liste des termes dont le nombre d'occurrences tombe dans cette place s'affichera dans la partie inférieure.",
            },
            "placement": "right",
            "position": "inside",
          },
          '#export_corpus':{
            "en":{"title":"Export",
                  "content":"You can export your corpus in <a target='_blank' href='https://iscpif.fr/gargantext/import-formats_en/'>CSV format</a>",
            },
            "fr":{
              "title": "Exporter",
              "content": "Vous pouvez exporter les données <a target='_blank'  href='https://iscpif.fr/gargantext/import-formats_fr/'>format CSV</a>",
              },
            "placement": "right",
            "position": "inside",

          },
          '#export_terms':{
            "en":{"title":"Export",
                  "content":"You can export your list of terms in <a target='_blank'  href='https://iscpif.fr/gargantext/import-formats_en/'>CSV format</a>.",
            },
            "fr":{
              "title": "Exporter",
              "content": "Vous pouvez exporter votre liste de termes au <a target='_blank'  href='https://iscpif.fr/gargantext/import-formats_fr/'>format CSV</a>",
            },
            "placement": "right",
            "position": "inside",
          },

          "#filter_analytics":{
            "en":{"title":"Filter documents",
                  "content":"You can filter the documents containing a certain type of data (words, authors, etc.) and see the changes in their number over time",
            },
            "fr":{
              "title": "Filtrer les documents",
              "content": "Vous pouvez filtrer les documents contenant un certain type de données (termes, auteurs, etc.) et consulter l'évolution de leur nombre au cours du temps",
            },
            "placement": "right",
            "position": "inside",
          },
          "#filter_terms":{
            "en":{"title":"Filter the terms",
                  "content": "<p>You can selectively filter and display different types of <b>lists</b>:<ul>"+
                    "<li><b>Stop list</b>:all expressions identified as irrelevant a priori (hollow words),</li>"+
                    "<li><b>Map list</b>:set of expressions which are the labels of the nodes of the thematic map. Each label can potentially combine several expressions (eg. Singular and plural).</li>"+
                    "<li><b>Others</b>: all well-formed expressions may be added to the thematic map.</li></ul></p>"+
                    "<p> You can also filter the <b> words </b> based on their form (they behave differently): <ul>"+
                    "<li> <b> 'One-word Terms </b>: select the terms that have a simple form </li>"+
                    "<li> <b> 'Multi-word Terms </ b>: select the words that have a compound form </li> </ul> </p>",
            },
            "fr":{
              "title": "Filtrer les termes",
              "content": "<p>Vous pouvez filtrer et afficher selectivement les différents types de <b>listes</b>:<ul>"+
                          "<li><b>Stop list</b>: toutes les expressions identifiées comme non pertinentes a priori (termes creux),</li>"+
                          "<li><b>Map list</b>: ensemble d'expressions qui consitueront les labels des noeuds de la carte thématique. Chaque label peut potentiellement regrouper plusieurs expressions (ex. singuliers et pluriels).</li>"+
                          "<li><b>Others</b>: ensemble d'expressions bien formées susceptibles d'être ajoutées à la carte thématique.</li></ul></p>"+
                          "<p>Vous pouvez aussi filtrer les <b>termes</b> en fonction de leur forme (ils se comportent différemment):<ul>"+
                          "<li><b>'One-word Terms'</b>: selectionner les termes qui ont une forme simple</li>"+
                          "<li><b>'Multi-word Terms'</b>: selectionner les termes qui ont une forme composée</li></ul></p>",
            },
            "placement": "right",
            "position": "inside",
          },

          "#edition":{
              "en":{
                "title":"Graph Edition and Manipulation Toolbar",
                "content":"Manipulate and edit your graph using this toolbar"+
                          "<ul>"+
                  				"<img src='/static/img/slider_edges.png'/>"+
                  				"<li>You can decide to  remove small nodes or large nodes using the"+
                  				"'nodes filter' slider (e.g. to get only the most popular"+
                  				"expressions):</li>"+
                  				"<img src='/static/img/slider_nodes.png'/>"+
                  				"<li>To change size of label (proportionnal to their strenght) use the 'label size slider':</li> "+
                          "<img src='/static/img/slider_label.png'/>"+
                  				"<li>Change cluster coloration using <label>'Colors'</label> button choosing in the options"+
                          "<img src='/static/img/slider_color.png'/>"+
                  				"<li>Change size of the nodes using <label>'Sizes'</label> button choosing in the options"+
                          "<img src='/static/img/slider_size.png'/>"+
                          "</ul>",

              },
              "fr":{
                "title":"Outil d'édition et de manipulation du graph",
                "content":"Manipuler and éditer le graph  grace à cette barre d'outil"+
                          "<ul>"+
                  				"<img src='/static/img/slider_edges.png'/>"+
                  				"<li>You can decide to  remove small nodes or large nodes using the"+
                  				"'nodes filter' slider (e.g. to get only the most popular"+
                  				"expressions):</li>"+
                  				"<img src='/static/img/slider_nodes.png'/>"+
                  				"<li>To change size of label (proportionnal to their strenght) use the 'label size slider':</li> "+
                          "<img src='/static/img/slider_label.png'/>"+
                  				"<li>Change cluster coloration using <label>'Colors'</label> button choosing in the options"+
                          "<img src='/static/img/slider_color.png'/>"+
                  				"<li>Change size of the nodes using <label>'Sizes'</label> button choosing in the options"+
                          "<img src='/static/img/slider_size.png'/>"+
                          "</ul>",

              },
              "placement": "right",
              "position": "inside",
          },
          "#exploration":{
            "en":{
            "title":"Graph Exploration Toolbar",
            "content":"<div>Explore your graph using this navigation bar"+
            "<ul>"+
    				"<a style='float: right;' class='btn-xs' href='#' id='lensButton'></a>"+
    				"<li>To center the graph, click on the center button. </li>"+
            "<a style='float: right;' class='btn-xs' href='#' id='edgesButton'></a>"+
            "<li>To calculate proximity measure and show the edges click on the button</li>"+
    				"<li>You can explore the graph using the slider and the  macro/mesolevel button."+
    				"<div class='inline'><a style='float: right;' class='small btn-xs' href='#' id='zoomPlusButton'></a>"+
    				"<a style='float: right;' class='small btn-xs' href='#' id='zoomMinusButton'></a></div>"+
            "</li></ul>",
              },
              "fr":{
              "title":"Outils d'exploration du Graphe",
              "content":"<div>Explorer le graph en utilisant cette barre d'outils"+
              "<ul>"+
      				"<a style='float: right;' class='btn-xs' href='#' id='lensButton'></a>"+
      				"<li>To center the graph, click on the center button. </li>"+
              "<a style='float: right;' class='btn-xs' href='#' id='edgesButton'></a>"+
              "<li>To calculate proximity measure and show the edges click on the button</li>"+
      				"<li>You can explore the graph using the slider and the  +/- button."+
      				"<div class='inline'><a style='float: right;' class='small btn-xs' href='#' id='zoomPlusButton'></a>"+
      				"<a style='float: right;' class='small btn-xs' href='#' id='zoomMinusButton'></a></div>"+
              "</li></ul>",
                },
          "placement": "right",
          "position": "inside",
          },
        }



//current lang
lang = $("a#lang").data("lang")
loadHelp(lang);

//change lang on click and load corresponding Help
$("a.new_lang").on("click", function(){
  //close all popover while changing lang
  $('.popover').popover('hide');
  old_lang = $("a#lang").data("lang")
  new_lang = $(this).data("lang")
  updateLang(lang, new_lang)
  loadHelp(new_lang)
});

function updateLang(old_lang, new_lang){
  console.log("Old", old_lang)
  console.log("Updating to", new_lang)

  //update lang in db via API
    $.ajax({
       url: '/api/user/parameters/',
       type: 'PUT',
       data: {"language":new_lang},
       beforeSend: function(xhr) {
             xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
                   },
      success: function(response, data) {
        console.log(data)
        var old_lang = $("a#lang").data("lang")
        //var new_lang = data["language"]


          //change active langue
        $("a#lang").attr("data-lang", new_lang);
        $("a#lang > img").attr({"value":new_lang, "src":"/static/img/"+new_lang+".png"})
        $("a#lang > span").text(new_lang)
          //switch lang to option
        $("a.new_lang").attr("data-lang", old_lang);
        $("a.new_lang > img").attr({"value":old_lang, "src":"/static/img/"+lang+".png"})
        $("a.new_lang > span").text(old_lang)
        console.log(response, data)
               },
          error: function(xhr) {
              console.log("EDIT FAIL!")
               },
          });

      console.log("defaut lang is now", $("a#lang").data("lang"))
};



function loadHelp(lang){
  $("img.help-btn").remove()
  $( ".help" ).each(function(i, el) {
    console.log("This", el);
    id = el.id
    div_id = "#"+id
    help_steps = Object.keys(help)
    //console.log(help_steps)
    //console.log("div help:", div_id)
    if (help_steps.includes(div_id) == false){
      console.log("Step #",id,"class='help' not described in help")
      return
    }
    btn = id+"-help"
    info = help[div_id]
    console.log(lang)
    console.log(info[lang]["content"])
    help_btn = '<img src="/static/img/question-mark.png" width="20px" height="20px"  class="help-btn" data-html="true" tab-index=0 data-container="body" data-toggle="popover" data-placement="'+info["placement"]+'"  title="'+info[lang]["title"]+'" data-content="'+info[lang]["content"]+'"></i>'

    console.log("position of the btn", info["position"])
    if (info["position"] == "inside"){
      $(help_btn).appendTo(el);
    }
    else if (info["position"] == "after"){
      $(help_btn).insertAfter(el);
    }
    else if (info["position"] == "before"){
      console.log("position", info["position"])
      //parent = $(el).parent()
      //help = $(help_btn).appendTo(el)
      //parent.prependTo(help)
      //console.log(">>>>>", $(this))
      $(help_btn).insertBefore(el);
    }
    else{
      //duplicate element and insert the button
      //$(help_btn).insertBefore(el);
    }

  });
}




$(document).on('click', function (e) {
    $('[data-toggle="popover"],[data-original-title]').each(function () {
        //the 'is' for buttons that trigger popups
        //the 'has' for icons within a button that triggers a popup
        if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
            (($(this).popover('hide').data('bs.popover')||{}).inState||{}).click = false  // fix for BS 3.3.6 data-trigger='focus' is a bug
        }

    });
});


function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie != '') {
      var cookies = document.cookie.split(';');
      for (var i = 0; i < cookies.length; i++) {
          var cookie = jQuery.trim(cookies[i]);
          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) == (name + '=')) {
              cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
              break;
          }
      }
  }
  return cookieValue;
};
