#!/bin/dash

#

echo "Copy nginx configuration in sites available"
sudo cp 4-NGINX_gargantext.conf /etc/nginx/sites-available

echo "Enable site"
cd /etc/nginx/sites-enable
sudo ln -s ../sites-available/gargantext.conf
sudo service nginx restart

echo "Copy UWSGI configuration"
sudo cp 4-UWSGI_gargantext.ini /etc/uwsgi/
sudo service uwsgi restart
