PYTHON ?= python
VERSION := $(shell cat VERSION)

.PHONY: check validate test review release clean

check: validate test

validate:
	$(PYTHON) scripts/validate.py

test:
	$(PYTHON) -m unittest discover -s tests

review:
	$(PYTHON) scripts/export_csv.py --output dist/csv
	$(PYTHON) scripts/export_excel.py --output dist/AMACS-$(VERSION)-review.xlsx

release: check review
	$(PYTHON) scripts/build_release.py --output dist/release

clean:
	rm -rf dist
