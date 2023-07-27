DATE    = $(shell date +"%F")

all:

docs:
	(cd doc; make html)
	(cd doc/html; zip -r ../pyRserve.html.zip *.html objects.inv searchindex.js _static/* )
	echo
	echo "Sphinx documentation has been created in doc/html/index.html"

clean:
	find . -name '*.pyc' -exec rm '{}' \;
	find . -name '*~'    -exec rm '{}' \;
	find . -name '*.bak' -exec rm '{}' \;
	find . -name '*.log' -exec rm '{}' \;
	find . -name '.coverage' -exec rm '{}' \;
	rm -rf build dist *.egg-info MANIFEST.in

upload-prep: docs
	rm -f dist/*
	python -m build
	twine check dist/*

upload: upload-prep
	twine upload dist/*

upload-testpypi: upload-prep
	twine upload -r testpypi dist/*

backup: clean _backup

_backup:
	DIR=`pwd`; bDIR=`basename $$DIR`; cd ..; \
	tar -czf $${bDIR}_$(DATE).tgz -X $$bDIR/TAR_EXCLUDELIST $$bDIR ; \
	echo "Created backup ../$${bDIR}_$(DATE).tgz"

test:
	pytest testing

coverage:
	rm -f pyRserve/binaryRExpressions.py*
	coverage run --source pyRserve -m pytest testing && coverage report --show-missing
