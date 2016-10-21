//Function that creates contextual help button
help = {"#project":{
          "title": "Ajouter un projet",
          "content":"Cliquez sur le bouton et donnez un nom à votre projet",
          "placement":"bottom",
          "position": "inside",
          },
        "#corpus":{
          "title": "Ajouter un corpus",
          "content": "<p>Pour ajouter un corpus à votre projet"+
                      "<br><b>Selectionnez une base de données</b>"+
                      "<ol><h4>&#x1f59b; Si vous avez déjà un fichier :</h4>"+
                      "<li>Vérifier que votre fichier est <a href=''>compressé au format .zip </a> et dans le bon <a href=''>format</a></li>"+
                      "<li>Cliquez sur 'Choisir un fichier...'</li>"+
                      "<li>Puis donnez un nom à votre corpus</li>"+
                      "<li>Cliquez sur 'Process this!'</li></ol>"+
                      "<ol><h4>&#x1f59b; Si vous souhaitez faire une recherche:</h4>"+
                      "<li>Sélectionnez l'option No à la question Do you have a file already?</li>"+
                      "<li>Entrez votre recherche</li>"+
                      "<li>Clickez ensuite sur Scan</li>"+
                      "<li>Une fois le nombre de résultats affichés, clickez sur 'Download!''</li>"+
                      "</ul>"+
                      "</p>",
          "placement": "right",
          "position": "inside",
          },
          '#docFilter':{
            "title": "Filtrer les documents",
            "content": "Vous pouvez afficher ici tous les documents, les favoris ou encore les doublons en selectionnant l'option dans le menu déroulant",
            "placement":"right",
            "position": "after",
          },
          '#titles_time':{
            "title": "Filtrer par date",
            "content": "Selectionnez une plage d'occurence sur une période spécifique en utilisant le curseur sur l'histogramme ci dessus."+
            "La répartition des documents et leur occurence  pour la période selectionnée s'affiche dans le graphe ci-dessous",
            "placement": "right",
            "position": "inside",
          },
          '#sources_time':{
            "title": "Filtrer par date",
            "content": "Selectionnez une plage d'occurence sur une période spécifique en utilisant le curseur sur l'histogramme ci dessus."+
            "La répartition des sources et leur occurence  pour la péridoe selectionnée s'affiche dans le graphe ci-dessous",
            "placement": "right",
            "position": "inside",
          },
          '#terms_time':{
            "title": "Filtrer par date",
            "content": "Selectionnez une plage d'occurence sur une période spécifique en utilisant le curseur sur l'histogramme ci dessus."+
            "La répartition des termes et leur occurence pour la période selectionnée s'affiche dans le graphe ci-dessous",
            "placement": "right",
            "position": "inside",
          },
          '#export_corpus':{
            "title": "Exporter",
            "content": "Vous pouvez exporter les données <a href=''>format CSV</a>",
            "placement": "right",
            "position": "inside",

          },
          '#export_terms':{
            "title": "Exporter",
            "content": "Vous pouvez exporter votre liste de termes <a href=''>format CSV</a>",
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
            "title": "Filtrer",
            "content": "Vous pouvez filtrer vos documents par expression de recherche et consulter leur évolution",
            "placement": "right",
            "position": "inside",
          },
          "#filter_terms":{
            "title": "Filtrer",
            "content": "<p>Vous pouvez filtrer et afficher <ul>les différentes <b>listes</b>:"+
            "<li>Stop list: tous les termes de la liste qui ont été écartés dans le graphe</li>"+
            "<li>Map list: tous les termes de la liste qui sont inclus dans le graphe</li>"+
            "<li>Other: les autres termes non blacklistés et non présents dans le graphe</li></ul></p>"+
            "<p>Vous pouvez aussi filtrer <ul>les <b>termes</b> en fonction de leur forme:"+
            "<li>'One-word Terms': selectionner les termes qui ont une forme simple</li>"+
            "<li>'Multi-word Terms': selectionner les termes qui ont une forme composée</li></ul></p>",
            "placement": "right",
            "position": "inside",
          },
          "#filter_graph":{
            "title": "Filtrer",
            "content": "Filtrer les arcs et les noeuds de votre graphe en fonction de leur poids. Utilisez la barre glissante",
            "placement": "right",
            "position":"after",
          }
        }

$( ".help" ).each(function(i, el) {

  console.log("This", el)
  id = el.id

  div_id = "#"+id
  help_steps = Object.keys(help)
  console.log(help_steps)
  console.log("div help:", div_id)
  if (help_steps.includes(div_id) == false){
    console.log("Step",id,"not described in help")
    return
  }
  btn = id+"-help"
  info = help[div_id]
  //console.log(info)
  help_btn = '<span class="glyphicon glyphicon-question-sign" tab-index=0 data-toggle="popover" data-placement="'+info["placement"]+'"  title="'+info["title"]+'" data-content="'+info["content"]+'"></span>'


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

})

$(document).on('click', function (e) {
    $('[data-toggle="popover"],[data-original-title]').each(function () {
        //the 'is' for buttons that trigger popups
        //the 'has' for icons within a button that triggers a popup
        if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
            (($(this).popover('hide').data('bs.popover')||{}).inState||{}).click = false  // fix for BS 3.3.6
        }

    });
});
