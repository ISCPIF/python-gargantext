#Install Instructions for Gargamelle:

Gargamelle is the gargantext plateforme toolbox it is a full plateform system
with minimal modules

First you need to get the source code to install it
The folder will be /srv/gargantext:
* docs containes all informations on gargantext
    /srv/gargantext/docs/
* install contains all the installation files
    /srv/gargantext/install/

Help needed ?
See [http://gargantext.org/about](http://gargantext.org/about) and [tools](./contribution_guide.md) for the community

## Get the source code

by cloning gargantext into /srv/gargantext

``` bash
git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
        && cd /srv/gargantext \
        && git fetch origin stable \
        && git checkout stable \
```


## Install
 ``` bash
 # go into the directory
 user@computer: cd /srv/gargantext/
 #git inside installation folder
 user@computer: cd /install
 #execute the installation
 user@computer: ./install
 ```
During installation an admin account for gargantext will be created by asking you a username and a password
Remember it to accès to the Gargantext plateform

## Run
Once you proceed to installation Gargantext plateforme will be available at localhost:8000
by running the run executable file
 ``` bash
 # go into the directory
 user@computer: cd /srv/gargantext/
 #git inside installation folder
 user@computer: cd /install
 #execute the installation
 user@computer: ./run
 #type ctrl+d to exit or exit; command
 ```

Then open up a chromium browser and go to localhost:8000
Click on "Enter Gargantext"
Login in with you created username and pasword

Enjoy! ;)




	
