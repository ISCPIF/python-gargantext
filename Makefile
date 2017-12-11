CELERY_INIT=./tools/init.d/gargantext-celery
POSTGREST_INIT=./tools/init.d/gargantext-postgrest

ifeq ("$(ENVIR)", "prod")
PIPENV_ARGS=
BACKEND_INIT=./tools/init.d/gargantext-uwsgi
else
ENVIR=dev
PIPENV_ARGS=--dev
BACKEND_INIT=./tools/init.d/gargantext-testserver
endif

PY_VERSION='import sys; v=sys.version_info; print("{0}.{1}".format(*v))'

.PHONY: default
default:
	@echo "Please specify a target."
	@echo "To setup environment: make ENVIR=$(ENVIR) setup"
	@echo "To start/stop/restart/reload/check: make ENVIR=$(ENVIR) {start|stop|restart|reload|check}"

.PHONY: setup
setup: venv conf migrate

.PHONY: venv
venv: envs
	@echo "• Setup virtualenv with all dependencies..."
	pipenv install $(PIPENV_ARGS)
	@# Put current directory in python path to be able to import gargantext
	@# from scripts in sub-directories (eg. alembic revisions)
	@pwd > $$(pipenv --venv)/lib/python$$($$(pipenv --py) -c $(PY_VERSION))/site-packages/gargantext.pth
	@echo

.PHONY: envs
envs:
	@echo "• Setup django settings module and configuration path..."
	./tools/mkenvs.sh
	@echo

.PHONY: migrate
migrate:
	@echo "• Migrate database to latest version..."
	pipenv run ./manage.py migrate
	pipenv run alembic upgrade head
	@echo

.PHONY: conf
conf:
	@echo "• Setup gargantext configuration..."
	./tools/mkconf.sh $(ENVIR)
	@echo

.PHONY: checkdebian
checkdebian:
	@./tools/checkdebian.sh

.PHONY: checkpipenv
checkpipenv:
	@./tools/checkpipenv.sh

.PHONY: checkstartup
checkstartup: checkdebian checkpipenv

.PHONY: start
start: checkstartup
	@echo "• Start gargantext servers..."
	@$(BACKEND_INIT) start
	@$(CELERY_INIT) start
	@$(POSTGREST_INIT) start
	@echo

.PHONY: stop
stop: checkstartup
	@echo "• Stop gargantext servers..."
	@$(BACKEND_INIT) stop
	@$(CELERY_INIT) stop
	@$(POSTGREST_INIT) stop
	@echo

.PHONY: restart
restart: checkstartup
	@echo "• Restart gargantext servers..."
	@$(BACKEND_INIT) restart
	@$(CELERY_INIT) restart
	@$(POSTGREST_INIT) restart
	@echo

.PHONY: reload
reload: checkstartup
	@echo "• Reload gargantext servers..."
	@$(BACKEND_INIT) reload
	@$(CELERY_INIT) force-reload
	@$(POSTGREST_INIT) reload
	@echo

.PHONY: check
check: checkstartup
	@echo "• Check gargantext servers..."
	@$(BACKEND_INIT) status || true
	@$(CELERY_INIT) status || true
	@$(POSTGREST_INIT) status || true
	@echo

.PHONY: status
status: check
