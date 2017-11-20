.PHONY: gargantext venv envs migrate conf

ifeq ($(TARGET), "prod")
TARG=prod
PIPENV_ARGS=
else
TARG=dev
PIPENV_ARGS=--dev
endif

PY_VERSION='import sys; v=sys.version_info; print("{0}.{1}".format(*v))'

gargantext: venv conf migrate

venv: envs
	@echo "• Setup virtualenv with all dependencies..."
	pipenv install $(PIPENV_ARGS)
	@# Put current directory in python path to be able to import gargantext
	@# from scripts in sub-directories (eg. alembic revisions)
	@pwd > $$(pipenv --venv)/lib/python$$($$(pipenv --py) -c $(PY_VERSION))/site-packages/gargantext.pth
	@echo

envs:
	@echo "• Setup django settings module and configuration path..."
	./tools/mkenvs.sh
	@echo

migrate:
	@echo "• Migrate database to latest version..."
	pipenv run ./manage.py migrate
	pipenv run alembic upgrade head
	@echo

conf:
	@echo "• Setup gargantext configuration..."
	./tools/mkconf.sh $(TARG)
	@echo
