# -*- coding: utf-8 -*-

# vim: tabstop=4 shiftwidth=4 autoindent noexpandtab

PYTHON=`which python`
NAME=`python setup.py --name`

all: check 

#init:
#	pip install -r requirements.txt --use-mirrors

#dist: source deb

source:
	pandoc -f markdown_github -t plain -o README.txt README.md
	$(PYTHON) setup.py sdist
	rm -rf rax_autoscaler.egg-info

upload2container: source
	date +"%y%m%d%H%M%S">dist/readme
	cd dist && echo rax-autoscaler*>>readme
	swift upload autoscale dist/rax-autoscaler*tar.gz dist/readme
	swift upload autoscale dist/readme

upload: source
	$(PYTHON) setup.py sdist upload

#deb:
#	$(PYTHON) setup.py --command-packages=stdeb.command bdist_deb

#rpm:
#	$(PYTHON) setup.py bdist_rpm --post-install=rpm/postinstall --pre-uninstall=rpm/preuninstall

test:
#	unit2 discover -s tests -t .
#	python -mpytest weasyprint
	nosetests --config=.noserc -xv

check:
	find . -name \*.py | grep -v 'conf.py' | xargs pep8 --max-line-length=100
	# pylint raxas --rcfile=.pylintrc
	# pyntch
	# pyflakes
	# pychecker
	# pymetrics

clean:
	rm -rf build/ MANIFEST dist build rax_autoscaler.egg-info deb_dist
	find . -name '*.pyc' -delete
	rm README.txt
	$(PYTHON) setup.py clean

#doc:
# Generate Sphinx documentation.
doc:
	cd docs && make clean && make html 
