sudo apt-get install postgresql
sudo apt-get install postgresql-contrib
sudo apt-get install python-virtualenv
sudo apt-get install libpng12-dev
sudo apt-get install libpng-dev
sudo apt-cache search freetype
sudo apt-get install libfreetype6-dev
sudo apt-cache search python-dev
sudo apt-get install python-dev
sudo apt-get install libpq-dev
sudo apt-get postgresql-contrib
sudo aptèget install libpq-dev

# Pour avoir toutes les dependences de matpolotlib (c'est sale, trouver
sudo apt-get build-dep python-matplotlib
#Paquets Debian a installer
# easy_install -U distribute (matplotlib)
#lxml
sudo apt-get install libffi-dev
sudo apt-get install libxml2-dev
sudo apt-get install libxslt1-dev

# ipython readline
sudo apt-get install libncurses5-dev
sudo apt-get install pandoc

# scipy:
sudo apt-get install gfortran
sudo apt-get install libopenblas-dev
sudo apt-get install liblapack-dev


source /srv/gargantext_env/bin/activate
pip3 install git+https://github.com/mathieurodic/aldjemy.git
