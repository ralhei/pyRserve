# Copyright (c) 2009, Symagon GmbH
# All rights reserved.
# www.symagon.com
#
# Use in source and binary forms, with or without modification, 
# is regulated by license agreements between Symagon and its licensees.
# Redistribution in source and binary forms prohibited.

DATE    = $(shell date +"%d%h%y")

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
	find . -name '*.so'  -exec rm '{}' \;
	find . -name '*.pyd' -exec rm '{}' \;
	find . -name '.coverage' -exec rm '{}' \;
	rm -rf build dist cdist_build py2q.egg-info MANIFEST.in

backup: clean _backup


_backup: 
	DIR=`pwd`; bDIR=`basename $$DIR`; cd ..; \
	tar -czf $${bDIR}_$(DATE).tgz -X $$bDIR/TAR_EXCLUDELIST $$bDIR ; \
	echo "Created backup ../$${bDIR}_$(DATE).tgz"


test:
	(cd py2q; py.test)

coverage:
	pyTest=`which py.test` ; \
	rm -f py2q/binaryQExpressions.py* ; \
	(cd py2q; coverage -e -x $${pyTest} ; coverage -r -m) 

