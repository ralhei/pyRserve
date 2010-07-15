DATE    = $(shell date +"%F")

all:

cdist:
	python setup.py cdist --templicense

ext:
	python setup.py build_ext --inplace


clean:
	find . -name '*.pyc' -exec rm '{}' \;
	find . -name '*~'    -exec rm '{}' \;
	find . -name '*.bak' -exec rm '{}' \;
	find . -name '*.log' -exec rm '{}' \;
	find . -name '.coverage' -exec rm '{}' \;
	rm -rf build dist *.egg-info MANIFEST.in

backup: clean _backup


_backup: 
	DIR=`pwd`; bDIR=`basename $$DIR`; cd ..; \
	tar -czf $${bDIR}_$(DATE).tgz -X $$bDIR/TAR_EXCLUDELIST $$bDIR ; \
	echo "Created backup ../$${bDIR}_$(DATE).tgz"


test:
	(cd  pyRserve; py.test)

coverage:
	pyTest=`which py.test` ; \
	rm -f pyRserve/binaryRExpressions.py* ; \
	(cd pyRserve; coverage run $${pyTest} ; coverage report -m) 

