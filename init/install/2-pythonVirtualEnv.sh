#!/bin/dash


sudo mkdir /srv/gargantext_env
sudo chown -R gargantua:www-data /srv/gargantext_env


pyvenv3 /srv/gargantext_env

source /srv/gargantext_env/bin/activate

pip install --upgrade pip
pip install -r 3-requirements.txt

pip3 install git+https://github.com/mathieurodic/aldjemy.git
patch /srv/gargantext_env/lib/python3.4/site-packages/cte_tree/models.py /srv/gargantext/init/cte_tree.models.diff



