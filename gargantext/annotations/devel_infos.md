ANNOTATIONS
===========

2016-01

## Routines de manipulation de ngrams dans les listes

#### Trajectoire globale des actions choisies

 1. angular: ngramlist.js (user input) or highlight.js (user menu controller)
 2. angular: http.js configuration object
    { 'action': 'post', 'listId': miamlist_id, ..}
 3. AJAX POST/DELETE
 4. "API locale" (=> annotations.views)
 5. DB insert/delete

Remarque:
Dans le code annotations d'Elias, il y a une "API locale" qui transmet les actions client vers le serveur.
  => l'interconnexion est configurée pour angular dans annotations/static/annotations/app.js qui lance son propre main sur la fenêtre en prenant les paramètres depuis l'url et en s'isolant de django
  => les routes amont sont définies pour django dans annotations.urls et reprises pour angular dans http.js


#### Par ex: l'étape AJAX pour suppression

`curl -XDELETE http://localhost:8000/annotations/lists/7129/ngrams/4497`

via annotations.views.NgramEdit.as_view())


#### ajout d'un ngram


```
curl -XPOST http://localhost:8000/annotations/lists/1866/ngrams/create \
     -H "Content-Type: application/json" \
     -d '{"text":"yooooooooo"}' > response_to_ngrams_create.html
```

## Points d'interaction côté client (GUI)

Add Ngram via dialog box :
 - controller:
   ngramlist.annotationsAppNgramList.controller('NgramInputController')
 - effect:
   1. NgramHttpService.post()

Add Ngram via select new + menu
 - controller: 
   highlight.annotationsAppHighlight.controller('TextSelectionMenuController')
     1. toggleMenu (sets action = X) 
     2. onMenuClick
 - effect:
   1. NgramHttpService[action]
