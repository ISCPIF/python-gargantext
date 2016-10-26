//Function that creates contextual help button
help = {"#project":{
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
            { "title":"Adding a project",
            "content": "Click on the button and give a name to your projet",
            },
          "fr":
            { "title": "Ajouter un corpus",
              "content": "<p>Pour ajouter un corpus à votre projet"+
                      "<br><b>Sélectionnez une base de données</b>"+
                      "<h4><span class='glyphicon glyphicon-hand-left'></span>  Si vous avez déjà un fichier à téléverser :</h4>"+
                      "<ol>"+
                      "<li>Vérifiez que votre fichier est <a href=''>compressé (archive .zip) </a> et dans le bon <a href='https://iscpif.fr/gargantext/import-formats'>format</a></li>"+
                      "<li>Cliquez sur 'Choisir un fichier...'</li>"+
                      "<li>Puis donnez un nom à votre corpus</li>"+
                      "<li>Cliquez sur 'Process this!'</li></ol>"+
                      "<h4><span class='glyphicon glyphicon-hand-left'>  Si vous souhaitez importer un corpus directement depuis une base de donnée ouverte (PubMed ou IsTex pour le moment):</h4>"+
                      "<ol>"+
                      "<li>Sélectionnez l'option No à la question Do you have a file already?</li>"+
                      "<li>Entrez votre requête (la syntaxe de la base de donnée cible est conservée)</li>"+
                      "<li>Cliquez ensuite sur 'Scan' pour avoir le nombre de résultats de votre requête</li>"+
                      "<li>Cliquez sur 'Download!' pour importer et analyser un échantillon</li>"+
                      "</ul>"+
                      "</p>",
                    },
          "placement": "right",
          "position": "inside",
          },
          '#docFilter':{
            "en":{
                "title":"Filter document",
                "content": ""
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
              "title":"",
              "content": ""
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
            "en":{},
            "fr":{
              "title": "Filtrer par nombre de publications",
              "content": "Selectionnez une plage de nombre minimal et maximal de publications par source en utilisant le curseur sur l'histogramme ci-dessus."+
              "Les sources correspondant à cette plage avec leur nombre de publications s'affichera dans la partie inférieure.",
            },
            "placement": "right",
            "position": "inside",
          },
          '#terms_time':{
            "en":{},
            "fr":{
              "title": "Filtrer occurrences",
              "content": "Selectionnez une plage d'occurences en utilisant le curseur sur l'histogramme ci dessus."+
                         "La liste des termes dont le nombre d'occurrences tombe dans cette place s'affichera dans la partie inférieure.",
            },
            "placement": "right",
            "position": "inside",
          },
          '#export_corpus':{
            "en":{},
            "fr":{
              "title": "Exporter",
              "content": "Vous pouvez exporter les données <a href=''>format CSV</a>",
              },
            "placement": "right",
            "position": "inside",

          },
          '#export_terms':{
            "en":{},
            "fr":{
              "title": "Exporter",
              "content": "Vous pouvez exporter votre liste de termes au format csv. <a href=''>format CSV</a>",
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
            "en":{},
            "fr":{
              "title": "Filtrer",
              "content": "Vous pouvez filtrer les documents contenant un certain type de données (termes, auteurs, etc.) et consulter l'évolution de leur nombre au cours du temps",
            },
            "placement": "right",
            "position": "inside",
          },
          "#filter_terms":{
            "en":{},
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
              "title":"",
              "content":"",
            },
            "fr":{
              "title": "Filtrer",
              "content": "Filtrer les arcs et les noeuds de votre graphe en fonction de leur poids. Utilisez chaque extremité glissante pour retirer les éléments les plus faibles (à gauche) ou les plus forts (à droite)",
            },
            "placement": "right",
            "position":"after",
          }
        };
//define lang
lang = $("a#lang").data("lang")
//change lang

$("a.new_lang").on("click", function(){

  new_lang = $(this).data("lang"))
  $
});


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
  help_btn = '<span class="glyphicon glyphicon-question-sign" tab-index=0 data-toggle="popover" data-placement="'+info[lang]["placement"]+'"  title="'+info[lang]["title"]+'" data-content="'+info[lang]["content"]+'"></span>'


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

$(document).on('click', function (e) {
    $('[data-toggle="popover"],[data-original-title]').each(function () {
        //the 'is' for buttons that trigger popups
        //the 'has' for icons within a button that triggers a popup
        if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
            (($(this).popover('hide').data('bs.popover')||{}).inState||{}).click = false  // fix for BS 3.3.6 data-trigger='focus' is a bug
        }

    });
});
