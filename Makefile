.PHONY: run install-deps

run: install-deps
	python3 main.py config.yaml

install-deps:
	@echo "==> Installing dependencies from requirements.txt…"
	python3 -m pip install --quiet -r requirements.txt

