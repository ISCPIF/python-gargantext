source /srv/gargantext_env/bin/activate
pip install git+https://github.com/mathieurodic/aldjemy.git
pip install djangorestframework==3.0.0
cd /srv/gargantext/
./manage.py syncdb
echo "Ok runserver!"


