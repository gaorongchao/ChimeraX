include ../Makefile.bundle

_WHEEL = $(wildcard dist/*.whl)

_install: _wheel
	$(RUN) "devel install $(_WHEEL) user false exit true $(DEBUG_ARG) $(INSTALL_ARGS)"

_wheel:
	python3 -m build

