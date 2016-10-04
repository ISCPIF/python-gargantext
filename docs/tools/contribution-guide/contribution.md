#Contribution guide

* A question or a problem? Ask the community
* Sources
* Tools
* Contribution workflow: for contributions, bugs and features
* Some examples of contributions

## Community
Need help? Ask the community
* [http://gargantext.org/about](http://gargantext.org/about)
* IRC Chat: (OFTC/FreeNode) #gargantex

## Source
Source are available throught XXX LICENSE

You can install Gargantext throught the [installation procedure](./install.md)

##Tools
* gogs
* forge.iscpif.fr
* server access
* gargantext box


## Contributing: workflow procedure
Once you have installed and tested Gargantext
You

1. Clone the stable release into your project
    Note: The current stable release <release_branch> is:  refactoring

Inside the repo, clone the reference branch and get the last changes:
git checkout <ref_branch>
git pull

It is highly recommended to create a generic branch on a stable release such as
git checkout -b <username>-<release_branch>
git pull


2. Create your project on stable release

git checkout -b <username>-<release_branch>-<project_name>

Do your modifications and commits as you want it:
git commit -m "foo/bar/1"
git commit -m "foo/bar/2"
git push


If you want to save your local change you can merge it into your generic branch <username>-<release_branch>
git checkout <username>-<release_branch>
git pull
git merge <username>-<release_branch>-<project_name>
git commit -m "[Merge OK] comment"


##Technical Overview

* Interface Overview

* Database Schema Overview

* Architecture Overview


### Exemple1: Adding a parser

### Exemple2: User Interface Design
