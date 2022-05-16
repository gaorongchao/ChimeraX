# === UCSF ChimeraX Copyright ===
# Copyright 2016 Regents of the University of California.
# All rights reserved.  This software provided pursuant to a
# license agreement containing restrictions on its disclosure,
# duplication and use.  For details see:
# http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html
# This notice must be embedded in or attached to all copies,
# including partial copies, of the software or any revisions
# or derivations thereof.
# === UCSF ChimeraX Copyright ===
all: wheel 

wheel: 
	python -m build 

install: wheel
	python -m pip install $(WHEEL)

app-install: wheel
	$(PYTHON_EXE) -m pip uninstall --yes $(BUNDLE_NAME)
	$(PYTHON_EXE) -m pip install $(WHEEL)

sync:
	rsync -av dist/*.whl $(TOP)/build/sync/

build: install
	# unlike normal bundles, install as well
	$(MAKE) sync

test:
	for t in $(wildcard test*.cxc) $(wildcard test*.py);\
		do $(CHIMERAX_EXE) --exit --nogui $$t;\
	done

clean:
	rm -rf src/__pycache__ build dist *.egg-info 

pylint:
	python -m flake8 src/
