* Create user gargantua
Main user of Gargantext is Gargantua (role of Pantagruel soon)!
``` bash
sudo adduser --disabled-password --gecos "" gargantua
```

* Create the directories you need

here for the example gargantext package will be installed in /srv/
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

You should see:

```bash
$tree /srv
/srv
├── gargantext
├── gargantext_lib
├── gargantext_media
│   └── srv
│       └── env_3-5
└── gargantext_static
```
* Get the main libraries

Download uncompress and make main user access to it.
PLease, Be patient due to the size of the packages libraries (27GO)
this step can be long....

``` bash
wget http://dl.gargantext.org/gargantext_lib.tar.bz2 \
&& tar xvjf gargantext_lib.tar.bz2 -o /srv/gargantext_lib \
&& sudo chown -R gargantua:gargantua /srv/gargantext_lib \
&& echo "Libs installed"
```

* Get the source code of Gargantext

by cloning the repository of gargantext
``` bash
git clone ssh://gitolite@delanoe.org:1979/gargantext /srv/gargantext \
        && cd /srv/gargantext \
        && git fetch origin refactoring \
        && git checkout refactoring \
```

    TODO(soon): git clone https://gogs.iscpif.fr/gargantext.git


See the [next steps of installation procedure](install.md#Install)
