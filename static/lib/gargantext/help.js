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
                        "<b><span class='glyphicon glyphicon-hand-right'>  If you want to import a corpus from an open database (only supported by PubMed or IsTex right now):</b>"+
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
                        "<b><span class='glyphicon glyphicon-hand-right'></span>  Si vous avez déjà un fichier à téléverser :</b>"+
                        "<ol>"+
                        "<li>Vérifiez que votre fichier est <a href='https://iscpif.fr/gargantext/import-formats_fr/'>compressé (archive .zip) </a> et dans le bon <a href='https://iscpif.fr/gargantext/import-formats'>format</a></li>"+
                        "<li>Cliquez sur 'Choisir un fichier...'</li>"+
                        "<li>Puis donnez un nom à votre corpus</li>"+
                        "<li>Cliquez sur 'Process this!'</li></ol>"+
                        "<b><span class='glyphicon glyphicon-hand-right'>  Si vous souhaitez importer un corpus directement depuis une base de donnée ouverte (PubMed ou IsTex pour le moment):</b>"+
                        "<ol>"+
                        "<li>Sélectionnez l'option No à la question Do you have a file already?</li>"+
                        "<li>Entrez votre requête (la syntaxe de la base de donnée cible est conservée)</li>"+
                        "<li>Cliquez ensuite sur 'Scan' pour avoir le nombre de résultats de votre requête</li>"+
                        "<li>Cliquez sur 'Download!' pour importer et analyser un échantillon prélevé de manière aléatoire</li>"+
                        "</ul>"+
                        "</p>",
                      },
            "placement": "bottom",
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
            "position": "after",
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
          // '#export_terms':{
          //   "title": "Exporter",
          //   "content": "Vous pouvez exporter votre liste de sources <a href=''>format CSV</a>",
          //   "placement": "right",
          //   "position": "after",
          //   "class":"push-right"
          // }
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
          "#filter_graph":{
            "en":{
              "title":"Filter edges and nodes of the graph",
              "content":"Filter the edges and nodes of your graph according to their weight. Use each slippery extremity to remove the weakest elements (left) or the strongest (right)",
            },
            "fr":{
              "title": "Filtrer les arcs et les noeuds du graph",
              "content": "Filtrer les arcs et les noeuds de votre graphe en fonction de leur poids. Utilisez chaque extremité glissante pour retirer les éléments les plus faibles (à gauche) ou les plus forts (à droite)",
            },
            "placement": "right",
            "position":"before",
          },
          // "#nodeweight":{
          //   "en":{
          //     "title": "Filter Nodes Weight",
          //     "content":  "Node sizes maps (on a log scale) correspond to the number of documents that"+
          //               "mention its label and its associated terms (if any). Filter node weight using the slider"
          //
          //   },
          //   "fr":{
          //     "title": "Filtrer les noeuds par leur poids",
          //     "content": "La taille des noeuds (sur une echelle logarithmique) correspond au nombre de documents qui mentionnent leur label et leur termes associés (s'ils sont associés). Filtrer les noeuds par leur poids",
          //   },
          //   "placement": "right",
          //   "position": "before",
          //
          //
          // },
          // "#edgeweight":{
          //   "en":{
          //     "title": "Filter Edges Weight",
          //     "content":  "Edges sizes maps"
          //
          //   },
          //   "fr":{
          //     "title": "Filtrer les arcs par leur poids",
          //     "content": "La taille des arcs ",
          //   },
          //   "placement": "right",
          //   "position": "before",
          //
          //
          // },
          // "#labelsize":{
          //   "en":{
          //     "title":"Filter Label Size",
          //     "content":"Filter on label size????",
          //
          //   },
          //   "fr":{
          //     "title": "Filtrer par la taille des labels",
          //     "content": "????",
          //
          //   },
          //   "placement": "right",
          //   "position": "before",
          // },
          // "#colorgraph":{
          //   "en":{
          //     "title":"Color cluster",
          //     "content":"Color clusters using options"
          //
          //   },
          //   "fr":{
          //     "title": "Colorer les clusters",
          //     "content":"Colorer les clusters en utilisant les options"
          //
          //   },
          //   "placement": "right",
          //   "position": "before",
          // },
          // "#sizegraph":{
          //   "en":{
          //     "title":"Size graph",
          //     "content":"Spatialize cluster using size options"
          //
          //   },
          //   "fr":{
          //     "title": "Size graph",
          //     "content":"Spatialize cluster using size options"
          //
          //   },
          //   "placement": "right",
          //   "position": "before",
          // },
          // "#selectorsize":{
          //   "en":{
          //     "title":"Selector size",
          //     "content":"Use the mouse on the graph to select nodes. Change the size of the selector"
          //
          //   },
          //   "fr":{
          //     "title":"Selector size",
          //     "content":"Use the mouse on the graph to select nodes. Change the size of the selector"
          //
          //   },
          //   "placement": "right",
          //   "position": "before",
          // },
          // "#addgraph":{
          //   "en":{
          //     "title":"Add results",
          //     "content":"Add next search results to current selection"
          //
          //   },
          //   "fr":{
          //     "title":"Ajouter",
          //     "content":"Ajouter les resultats de la recherche à la selection active"
          //
          //   },
          //   "placement": "right",
          //   "position": "inside",
          // },
          // "#search":{
          //   "en":{
          //     "title":"Search in corpus",
          //     "content":"Search nodes in graph: results will show the corresponding documents in corpus"
          //
          //   },
          //   "fr":{
          //     "title":"rechercher dans le corpus",
          //     "content":"Rechercher les noeuds du graph:les resultats montreront leur emploi dans le corpus"
          //
          //   },
          //   "placement": "top",
          //   "position": "inside",
          // },
          // "#unfold":{
          //   "type": "slider-content",
          //   "en":{
          //     "title":"Search in corpus",
          //     "content":"Search nodes in graph: results will show the corresponding documents in corpus"
          //
          //   },
          //   "fr":{
          //     "title":"rechercher dans le corpus",
          //     "content":"Rechercher les noeuds du graph:les resultats montreront leur emploi dans le corpus"
          //
          //   },
          //   "placement": "top",
          //   "position": "inside",
          // },
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

  //update lang in db
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
    help_btn = '<img src="/static/img/question-mark.png" width="20px" height="20px"  class="help-btn" data-html="true" tab-index=0 data-container="body" data-toggle="popover" data-placement="'+info[lang]["placement"]+'"  title="'+info[lang]["title"]+'" data-content="'+info[lang]["content"]+'"></i>'


    if (info["position"] == "inside"){
      $(help_btn).appendTo(el);
    }
    else if (info["position"] == "after"){
      $(help_btn).insertAfter(el);
    }
    else if (info["position"] == "before"){
      $(help_btn).insertBefore(el);
    }
    else if (info["position"] == "dup_child"){
      //copy the first child inside the element and create a custom one with btn
      console.log(el.children())
    }
    else if (info["position"] == "dup_parent"){
      //copy the element and create a copy with btn
      console.log(el.parent())
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
