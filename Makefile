.PHONY: gargantext env conf

ifeq ($(TARGET), "prod")
TARG=prod
PIPENV_ARGS=
else
TARG=dev
PIPENV_ARGS=--dev
endif

gargantext: conf env
	@echo "• Installing dependencies..."
	pipenv install $(PIPENV_ARGS)
	@echo

env:
	@echo "• Setup django settings module and configuration path..."
	./tools/mkenv.sh
	@echo

conf:
	@echo "• Setup gargantext configuration..."
	./tools/mkconf.sh $(TARG)
	@echo
