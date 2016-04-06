# Gargantext Annotations web application

We also use a number of node.js tools to initialize and test. You must have node.js and
its package manager (npm) installed.  You can get them from [http://nodejs.org/](http://nodejs.org/).

## Preview only

Activate your virtualenv and run a simple http server

```
workon gargantext
python3 -m http.server
```
or :

```
npm start
```

Now browse to the app at `http://localhost:8000/app/index.html`.

## Install development tools and dependencies


We have two kinds of dependencies in this project: tools and angular framework code.  The tools help
us manage and test the application.

* We get the tools we depend upon via `npm`, the [node package manager][npm].
* We get the angular code via `bower`, a [client-side code package manager][bower].

We have preconfigured `npm` to automatically run `bower` so we can simply do:

```
npm install
```

Behind the scenes this will also call `bower install`.  You should find that you have two new
folders in your project.

* `node_modules` - contains the npm packages for the tools we need
* `app/bower_components` - contains the angular framework files

*Note that the `bower_components` folder would normally be installed in the root folder but
angular-seed changes this location through the `.bowerrc` file.  Putting it in the app folder makes
it easier to serve the files by a webserver.*


## Directory Layout


This will be adapted to fit the django API code as well. For now, the generic layout is :

```
app/                    --> all of the source files for the application
  app.css               --> default stylesheet
  components/           --> all app specific modules
  view1/                --> the view1 view template and logic
    view1.html            --> the partial template
    view1.js              --> the controller logic
    view1_test.js         --> tests of the controller
  app.js                --> main application module
  index.html            --> app layout file (the main html template file of the app)
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


## Updating the web application

Previously we recommended that you merge in changes to angular-seed into your own fork of the project.
Now that the angular framework library code and tools are acquired through package managers (npm and
bower) you can use these tools instead to update the dependencies.

You can update the tool dependencies by running:

```
npm update
```

This will find the latest versions that match the version ranges specified in the `package.json` file.

You can update the Angular dependencies by running:

```
bower update
```

This will find the latest versions that match the version ranges specified in the `bower.json` file.



### Running the App in Production

This really depends on how complex your app is and the overall infrastructure of your system, but
the general rule is that all you need in production are all the files under the `app/` directory.
Everything else should be omitted.

Angular apps are really just a bunch of static html, css and js files that just need to be hosted
somewhere they can be accessed by browsers.

If your Angular app is talking to the backend server via xhr or other means, you need to figure
out what is the best way to host the static files to comply with the same origin policy if
applicable. Usually this is done by hosting the files by the backend server or through
reverse-proxying the backend server(s) and webserver(s).


##

[AngularJS]: http://angularjs.org/
[git]: http://git-scm.com/
[bower]: http://bower.io
[npm]: https://www.npmjs.org/
[node]: http://nodejs.org
[protractor]: https://github.com/angular/protractor
[jasmine]: http://jasmine.github.io
[karma]: http://karma-runner.github.io
[http-server]: https://github.com/nodeapps/http-server
