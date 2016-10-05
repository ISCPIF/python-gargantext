# Install Instructions for Gargamelle

**Gargamelle** is the gargantext platform toolbox: it installs a full gargantext system with minimal modules inside a **docker** container.

First you need to get the source code to install it  
The destination folder will be `/srv/gargantext`:
* docs contains all information on gargantext  
    (`/srv/gargantext/docs/`)
* install contains all the installation files  
    `/srv/gargantext/install/`

Help needed ?  
See [http://gargantext.org/about](http://gargantext.org/about) and [tools](./contribution_guide.md) for the community

## Get the source code

by cloning gargantext into /srv/gargantext

``` bash
git clone ssh://git@gitlab.iscpif.fr:20022/humanities/gargantext.git /srv/gargantext \
        && cd /srv/gargantext \
        && git fetch origin install \
        && git checkout install \
```


## Install
 ``` bash
# go into the directory
user@computer: cd /srv/gargantext/
# get inside installation folder
user@computer: cd install
# execute the installation script
user@computer: ./install
 ```

During installation an admin account for gargantext will be created by asking you a username and a password  
Remember it to access to the Gargantext plateform

## Run
Once you're done with the installation, **Gargantext** platform will be available at `http://localhost:8000`
simply by running the `start` executable file
``` bash
# go into the directory
user@computer: cd /srv/gargantext/
# run the start command
user@computer: ./start
# type ctrl+d or "exit" command to exit
```

Then open up a chromium browser and go to `http://localhost:8000`  
Click on "Enter Gargantext"  
Login in with your created username and password  

Enjoy! ;)
