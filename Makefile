.PHONY: dev prod env conf

dev: conf env
	@echo "• Installing dependencies..."
	pipenv install --dev
	@echo

prod: conf env
	@echo "• Installing dependencies..."
	pipenv install
	@echo

env:
	@echo "• Setup django settings module..."
	./tools/mkenv.sh
	@echo

conf:
	@echo "• Setup gargantext configuration..."
	./tools/mkconf.sh
	@echo
