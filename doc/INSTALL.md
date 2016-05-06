#INSTALL

## Clone  the repositority
(For now git clone ssh://gitolite@delanoe.org:1979/gargantext)
copy the workibg branch
git fetch origin refactoring
create your own branch if you want to contribute
git checkout -b username-refact refactoring

## Installation instruction
are detailled in gargantex/install
create a default user for granatext: gargantua

``` bash
sudo adduser --disabled-password --gecos "" gargantua
```
create the different directory for Gargantex
``` bash
for dir in "/srv/gargantext"
           "/srv/gargantext_lib"
           "/srv/gargantext_static"
           "/srv/gargantext_media"
           "/srv/env_3-5"; do
    sudo mkdir -p $dir ;
    sudo chown gargantua:gargantua $dir ;
done
```

You should have:

```bash
tree /srv
/srv
├── gargantext
├── gargantext_lib
├── gargantext_media
│   └── srv
│       └── env_3-5
├── gargantext_static
└── lost+found [error opening dir]

```
