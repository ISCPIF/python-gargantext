Here informations for installation:

I - Local Installation

All informations are in init folder

1) Create virtualenv with python version 3.4

2) pip install -r requirements.txt

3) Manually install nltk (inside the sources)
	nltk==3.0a4

4) adapt database configuration in gargantext_web settings 
(Development done on postgresql)

5) source env/bin/activate

6) ./manage.py runserver

That's all
