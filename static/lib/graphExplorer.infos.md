Remarques sur l'intégration de tina
===================================

### Pour info: procédure suivie

Je copie ici les 2 commandes utilisées pour rendre visible comment a été faite la fusion du git de tina dans celui de garg.

Grace à cette méthode, quand on clonera le dépot gargantext, on obtiendra aussi les contenus du dépôt tina dans notre sous-dossier **`static/lib/graphExplorer`**.

**NB**  
Il n'est pas nécessaire de refaire cette procédure, dorénavant les fichiers restent là dans le sous-dossier.


  1. on a ajouté le dépôt extérieur de graphExplorer comme si c'était une remote normale  
     ```
     git remote add dependancy_graphExplorer_garg https://gogs.iscpif.fr/humanities/graphExplorer_garg
     ```

  2. on a lancé la commande `subtree` avec cette remote, pour récupérer le dépôt tina et le placer dans garg dans le dossier indiqué par l'option `prefix`

    ```
    git subtree add --prefix=static/lib/graphExplorer dependancy_graphExplorer_garg master
    ```

    Résultat:
    ```
    # git fetch dependancy_graphExplorer_garg master
    # (...)
    # Receiving objects: 100% (544/544), 1.72 MiB | 0 bytes/s, done.
    # Resolving deltas: 100% (307/307), done.
    # From https://gogs.iscpif.fr/humanities/graphExplorer_garg
    #  * branch            master     -> FETCH_HEAD
    #  * [new branch]      master     -> dependancy_graphExplorer_garg/master
    # Added dir 'static/lib/graphExplorer'
    ```

  3. au passage la même commande a aussi créé le commit suivant dans ma branche gargantext
    ```
    # commit b8d7f061f8c236bad390eb968d153fd6729b7434
    # Merge: 3bfb707 d256049
    # Author: rloth <romain.loth@iscpif.fr>
    # Date:   Thu Jul 7 16:01:46 2016 +0200
    #
    #     Add 'static/lib/graphExplorer/' from commit 'd256049'
    ```
    (ici le commit *d256049* indique le point où en était le dépôt tina quand il a été copié)


### Utilisation en développement quotidien

Il n'y a plus rien de particulier à faire. Le dossier contient les éléments de tina qui nous sont nécessaires. On peut ignorer l'existence du subtree et travailler normalement, dans ce dossier et ailleurs.

**=> nos opérations de commit / pull quotidiennes ne sont pas affectées**

Il n'est pas non plus nécessaire de prendre en compte la présence ou l'absence de la "remote" (lien extérieur) dans son travail.

### Utilisation avancée: pour propager les résultats entre dépôts

A présent le dépôt tina peut être vu comme une sorte de dépôt upstream circonscrit à un seul sous-dossier **`static/lib/graphExplorer`** !

Mais si des changements interviennent dans le dépôt tina, ils ne seront pas automatiquement intégrés dans sa copie intégrée à garg. Pour opérer des A/R entre les dépôts le plus simple est une 1ère fois d'ajouter le même pointeur extérieur :
```
git remote add dependancy_graphExplorer_garg https://gogs.iscpif.fr/humanities/graphExplorer_garg
```

A partir de là, il devient très simple de faire des opérations push/pull entre dépôts si besoin est..

  1. Récupération de mises à jour tina => garg.
     Pour intégrer des changements upstream de tina vers garg, il suffit de lancer la commande suivante:

    ```
    git subtree pull --prefix=static/lib/graphExplorer dependancy_graphExplorer_garg master --squash
    ```

  2. Inversement, les changements effectués dans le dossier **`static/lib/graphExplorer`** par les développeurs garg peuvent aussi être poussés du dépôt garg vers le dépôt tina par un subtree push
    ```
    git subtree push --prefix=static/lib/graphExplorer dependancy_graphExplorer_garg master
    ```
