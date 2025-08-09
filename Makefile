PY := python3

run: install-deps
	$(PY) analyse.py $(file)

install-deps:
	@echo "==> Устанавливаю/обновляю pipreqs…"
	$(PY) -m pip install --quiet --upgrade pipreqs
	@echo "==> Генерирую requirements.txt…"
	# Сначала пробуем бинарь, если нет — через модуль
	pipreqs . --force || $(PY) -m pipreqs.pipreqs . --force
	@echo "==> Ставлю зависимости…"
	$(PY) -m pip install --quiet -r requirements.txt

clear-run:
	$(PY) analyse.py $(file)