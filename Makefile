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
	@for f in tests/test*.py; do python $$f; done

integration:
	python tests/integration.py

coverage:
	nosetests --cover-package=librato --cover-erase --cover-html --with-coverage
	@echo ">> open "file:///"`pwd`/cover/index.html"

tox:
	tox

publish:
	@sh/publish.sh

clean:
	find . -name "*.pyc" | xargs rm -f
	rm -rf tests/__pycache__ librato_metrics.egg-info htmlcov .coverage dist cover
