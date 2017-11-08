.PHONY: dev prod env

dev: env
	@echo "• Installing dependencies..."
	pipenv install --dev
	@echo

prod: env
	@echo "• Installing dependencies..."
	pipenv install
	@echo

env:
	@echo "• Setup django settings module..."
	./tools/mkenv.sh
	@echo
