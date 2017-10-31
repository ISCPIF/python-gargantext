# Gargantext Annotations web application

## Install dependencies

(2016-05-11) Instead of the previously "npm-installable" structure, all the libraries are now permanently installed outside of the app 'annotations', directly in the 'static' dir of the entire gargantext project.

Initial version specifications of the dependencies are:
  - "angular": "~1.2.x",
  - "angular-cookies": "~1.2.x",
  - "angular-loader": "~1.2.x",
  - "angular-resource": "~1.2.x",
  - "bootstrap": "~3.x",
  - "angular-cookies": "1.2",
  - "bootstrap-select": "silviomoreto/bootstrap-select#~1.7.3"
  - "underscore": "1.5.2"

These dependencies are imported via annotations/main.js (js) and main.html (css).

## Directory Layout


The layout is :

```
├── __init__.py
├── README.md
├── static
│   └── annotations
│       ├── activelists.js
│       ├── app.css
│       ├── app.js
│       ├── document.js
│       ├── highlight.js
│       ├── http.js
│       ├── keyword_tpl.html
│       ├── main.js
│       ├── ngramlist.js
│       └── utils.js
├── templates
│   └── annotations
│       └── main.html
├── urls.py
└── views.py

```


# Conception and workflow documentation

## TODO : à traduire en anglais

Cette API permet d'éditer les mots-clés miamlistés ou stoplistés associé à un document affiché dans un cadre d'une page web permettant de naviguer à travers un ensemble de document d'un corpus.

### Architecture

- Templates : Django et Angular.js ?
- Communication entre les modules : évènements Angular ($emit et $broadcast)
- Pas de routage entre différentes URL, car ici une seule vue principale basée sur le template django corpus.html
- Modèle d'abstraction de données : côté client (Angular Scopes) et côté serveur (Django Model et SQLAlchemy)
- Composants : TODO lister et décrire les composants client et serveur
- Structure de l'application : organisation du client et du serveur
- Style : Bootstrap et un thème spécifique choisi pour Gargantext
- Gestion des dépendances :
  - bower, npm pour le développement web et les tests côté client
  - pip requirements pour le côté serveur

## Quelles actions execute l'API ?

- afficher le titre, les auteurs, le résumé, la date de publication et le corps d'un document.
- lecture des mots-clés miamlistés associés à un document (dans le texte et hors du texte).
- lecture des mots-clés stoplistés associés à un document (dans le texte et hors du texte).
- lecture des documents ayant le plus de mots-clés miamlistés associés identiques pour afficher une liste de liens vers de nouveaux documents
- lecture du groupe de mots-clés auquel appartient un mot-clé (synonymes, différentes formes)
- modification du groupe de mots-clés auquel appartient un mot-clé donné

On désigne par mot-clé un NGram.

## Schéma de l'API

Liste des endpoints

### Lecture des données

- POST '^api/nodes/(\d+)/children/queries$' : liste des NGrams d'un document avec la possibilité de filtrer par NGrams
- GET '^api/nodes$' : liste des identifiants de mots-clés filtrés par type (NGram ou autre) pour un identifiant de parent (Document ou autre)
- GET '^api/nodes/(\d+)/ngrams$': liste des termes des mots-clés associés à un Document parent, filtrés par termes
- GET ^api/nodes/(\d+)/children/metadata$ : liste des metadata d'un Node, c'est-à-dire :
  - pour un document : titre, auteur, etc
  - pour un NGram : stoplisté ou miamlisté ?

### Écriture des données

TODO

## Workflow

Nous nous fixons sur cette documentation et spécification de l'API

- en parallèle : développement de l'API et prototypage de l'interface
- le prototypage de l'interface peut modifier l'API si besoin

### Spécifications des fondations de l'interface

- résolutions d'écran
- browsers
- langue: english only
- SEO: aucun ?
- collaboratif : oui, les modifications d'un autre utilisateurs seront notifiées à tous les utilisateurs présent sur le même corpus de documents
- fonctionne offline ?

### Working process

- follow board is updated regularly (https://trello.com/b/96ItkDBS/gargantext-miamlists-and-stoplists)[on Trello]

- calendrier prévisionnel: TODO
- interactions entre les acteurs: emails
- git, branches : branche "elias", `git pull --rebase origin master` réguliers
- prévision des revues de code et de l'interface : TODO

### Plateforme

- Python 3.4
- Django 1.6
- Postgresql 9.3 + HSTORE
- SQLAlchemy
- Bootstrap CSS
- Angular.js

### Outils de qualité de code

- pylint
- jshint (voir .jshintrc)
- indentations : 4 espaces (voir .lvimrc)
- nettoyage automatique des espaces en fin de ligne

## Tests

There are two kinds of tests possible : Unit tests and End to End tests.

- côté client : étudier karma.js et protractor
- définir la stratégie de tests : TODO

## Déploiement

- définir le processus de déploiement
- prévoir un système de monitoring des erreurs du serveur une fois en ligne
    - Sentry ?
