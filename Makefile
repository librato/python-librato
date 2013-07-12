SHELL := /bin/bash
.PHONY: targets utests integration clean coverage publish tox

targets:
	@echo "make utests     : Unit testing"
	@echo "make integration: Integration tests "
	@echo "make coverage   : Generate coverage stats"
	@echo "make tox        : run tox (runs unit tests using different python versions)"
	@echo "make publish    : publish a new version of the package"
	@echo "make clean      : Clean garbage"

utests:
	python tests/test_basic.py

integration:
	python tests/integration.py

coverage:
	coverage run tests/test_basic.py
	coverage html
	coverage report -m
	@echo ">> open htmlcov/index.html"

tox:
	tox

publish:
	@(\
	export ONE=`cat setup.py | grep "version" | ruby -ne 'puts $$_.match(/([\d\.]+)\"/)[1]'`; \
	export TWO=`cat librato/__init__.py | grep "^__version__" | ruby -ne 'puts $$_.match(/([\d\.]+)\"/)[1]'`; \
	echo "Current version: $$ONE $$TWO"; \
	echo -ne "Introduce new version: "; \
	read NEW;\
	export _NEW=$$NEW; \
	echo "New version will be: $$NEW"; \
	cat setup.py            | ruby -ne 'puts $$_.gsub(/([\d\.]+\")/, ENV["_NEW"] + "\"" )'	> _tmp ; \
	cat librato/__init__.py | ruby -ne 'puts $$_.gsub(/([\d\.]+\")/, ENV["_NEW"] + "\"" )'  > _tmp2 ; \
	mv _tmp setup.py ;\
	mv _tmp2 librato/__init__.py ;\
	python setup.py sdist upload ;\
	rm -f _tmp _tmp2;\
	)

clean:
	find . -name "*.pyc" | xargs rm -f
	rm -rf tests/__pycache__ librato_metrics.egg-info htmlcov .coverage dist
