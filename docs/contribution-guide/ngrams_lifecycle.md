Cycle de vie des décomptes ngrammes
-----------------------------------

### (schéma actuel et pistes) ###

Dans ce qui crée les décomptes, on peut distinguer deux niveaux ou étapes:

1.  l'extraction initiale et le stockage du poids de la relation ngramme
    document (appelons ces nodes "1doc")

2.  tout le reste: la préparation des décomptes agrégés pour la table
    termes ("stats"), et pour les tables de travail des graphes et de la
    recherche de publications.

On pourrait peut-être parler d'indexation par docs pour le niveau 1 et de "modélisations" pour le niveau 2.

On peut remarquer que le niveau 1 concerne des **formes** ou ngrammes seuls (la forme observée <=> chaine de caractères u-nique après normalisation) tandis que dans le niveau 2 on a des objets plus riches... Au fur et à mesure des traitements on a finalement toujours des ngrammes mais:

  - filtrés (on ne calcule pas tout sur tout)

  - typés avec les listes map, stop, main (et peut-être bientôt des
    "ownlistes" utilisateur)...

  - groupés (ce qu'on voit avec le `+` de la table terme, et qu'on
    pourrait peut-être faire apparaître aussi côté graphe?)

On peut dire qu'on manipule plutôt des **termes** au niveau 2 et non plus des **formes**... ils sont toujours des ngrammes mais enrichis par l'inclusion dans une série de mini modèles (agrégations et typologie de ngrammes guidée par les usages).

### Tables en BDD

Si on adopte cette distinction entre formes et termes, ça permet de clarifier à quel moment on doit mettre à jour ce qu'on a dans les tables. Côté structure de données, les décomptes sont toujours stockés via des n-uplets qu'on peut du coup résumer comme cela:

-   **1doc**: (doc:node - forme:ngr - poids:float) dans des tables
    NodeNgram

-   **occs/gen/spec/tirank**: (type_mesure:node - terme:ngr -
    poids:float) dans des tables NodeNgram

-   **cooc**: (type_graphe:node - terme1:ngr - terme2:ngr -
    poids:float) dans des tables NodeNgramNgram

-   **tfidf**: (type_lienspublis:node - doc:node - terme:ngr -
    correlation:float) dans des tables NodeNodeNgram.

Où "type" est le node portant la nature de la stat obtenue, ou bien la
ref du graphe pour cooc et de l'index lié à la recherche de publis pour
le tfidf.

Il y a aussi les relations qui ne contiennent pas de décomptes mais sont
essentielles pour former les décomptes des autres:

-   map/main/stopliste: (type_liste:node - forme ou terme:ngr) dans des
    tables NodeNgram

-   "groupes": (mainform:ngr - subform:ngr) dans des tables
    NodeNgramNgram.

### Scénarios d'actualisation

Alors, dans le déroulé des "scénarios utilisateurs", il y plusieurs
évenements qui viennent **modifier ces décomptes**:

1.  les créations de termes opérés par l'utilisateur (ex: par
    sélection/ajout dans la vue annotation)

2.  les imports de termes correspondant à des formes jamais indexées sur
    ce corpus

3.  les dégroupements de termes opérés par l'utilisateur

4.  le passage d'un terme de la stopliste aux autres listes

5.  tout autre changement de listes et/ou création de nouveaux
    groupes...

A et B sont les deux seules étapes hormis l'extraction initiale où des
formes sont rajoutées. Actuellement A et B sont gérés tout de suite pour
le niveau 1 (tables par doc) : il me semble qu'il est bon d'opérer la
ré-indexation des 1doc le plus tôt possible après A ou B. Pour la vue
annotations, l'utilisateur s'attend à voir apparaître le surlignage
immédiatement sur le doc visualisé. Pour l'import B, c'est pratique car
on a la liste des nouveaux termes sous la main, ça évite de la stocker
quelque part en attendant un recalcul ultérieur.

L'autre info mise à jour tout de suite pour A et B est l'appartenance
aux listes et aux groupes (pour B), qui ne demandent aucun calcul.

C, D et E n'affectent pas le niveau 1 (tables par docs) car ils ne
rajoutent pas de formes nouvelles, mais constituent des modifications
sur les listes et les groupes, et devront donc provoquer une
modification du tfidf (pour cela on doit passer par un re-calcul) et des
coocs sur map (effet appliqué à la demande d'un nouveau graphe).

C et D demandent aussi une mise à jour des stats par termes
(occurrences, gen/spec etc) puisque les éléments subforms et les
éléments de la stopliste ne figurent pas dans les stats.

Donc pour résumer on a dans tous les cas:

=> l'ajout à une liste, à un groupe et tout éventuel décompte de
nouvelle forme dans les docs sont gérés dès l'action utilisateur

=> mais les modélisations plus "avancées" représentées par les les
stats occs, gen, spec et les tables de travail "coocs sur map" et
"tfidf" doivent attendre un recalcul.

Idéalement à l'avenir il seraient tous mis à jour incrémentalement au
lieu de forcer ce recalcul... mais pour l'instant on en est là.

### Fonctions associées

|       |                          GUI                          |                                       API action → url                                        |                      VIEW                       |                                                            SUBROUTINES                                                             |
|-------|-------------------------------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| A     | "annotations/highlight.js, annotations/ngramlists.js" | "PUT → api/ngrams, PUT/DEL → api/ngramlists/change"                                           | "ApiNgrams, ListChange"                         | util.toolchain.ngrams_addition.index_new_ngrams                                                                                    |
| B     | NGrams_dyna_chart_and_table                           | POST/PATCH → api/ngramlists/import                                                            | CSVLists                                        | "util.ngramlists_tools.import_ngramlists, util.ngramlists_tools.merge_ngramlists, util.toolchain.ngrams_addition.index_new_ngrams" |
| C,D,E | NGrams_dyna_chart_and_table                           | "PUT/DEL → api/ngramlists/change,  PUT/DEL → api/ngramlists/groups" "ListChange, GroupChange" | util.toolchain.ngrams_addition.index_new_ngrams |                                                                                                                                    |

L'import B a été remis en route il y a quelques semaines, et je viens de
reconnecter A dans la vue annotations.
