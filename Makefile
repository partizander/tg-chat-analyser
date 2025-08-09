PY := python3

run: install-deps
	$(PY) analyse.py $(file)

install-deps:
	@echo "==> Installing/updating pipreqs…"
	$(PY) -m pip install --quiet --upgrade pipreqs
	@echo "==> Generating requirements.txt…"
	# First try the binary, if not — via the module
	pipreqs . --force || $(PY) -m pipreqs.pipreqs . --force
	@echo "==> Installing dependencies…"
	$(PY) -m pip install --quiet -r requirements.txt

clear-run:
	$(PY) main.py
