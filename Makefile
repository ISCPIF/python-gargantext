.PHONY: gargantext env conf

ifeq ($(TARGET), "prod")
TARG=prod
PIPENV_ARGS=
else
TARG=dev
PIPENV_ARGS=--dev
endif

VENV=$(shell pipenv --venv)
PY_VERSION=$(shell python -c 'import sys; v=sys.version_info; print("{0}.{1}".format(*v))')

gargantext: conf env
	@echo "• Installing dependencies..."
	pipenv install $(PIPENV_ARGS)
	@# Put current directory in python path to be able to import gargantext
	@# from scripts in sub-directories (eg. alembic revisions)
	@pwd > $(VENV)/lib/python$(PY_VERSION)/site-packages/gargantext.pth
	@echo

env:
	@echo "• Setup django settings module and configuration path..."
	./tools/mkenv.sh
	@echo

conf:
	@echo "• Setup gargantext configuration..."
	./tools/mkconf.sh $(TARG)
	@echo
