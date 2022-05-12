TOP	= ../..
include $(TOP)/mk/config.make

CHIMERAX_APP = $(realpath $(wildcard $(TOP)/ChimeraX*.app))
SEGGER_SRC = seggerx_2022_05_11_modified_topdir.tar.gz

install app-install: seggerx
	$(MAKE) -C seggerx/Segger install

seggerx: $(SEGGER_SRC)
	tar xf $(SEGGER_SRC)
	touch seggerx

$(SEGGER_SRC):
	$(FETCH_PREREQ) $(PREREQS_ARCHIVE)/segger/$(SEGGER_SRC)

upload_new_version:
	$(RSYNC) $(SEGGER_SRC) $(PREREQS_UPLOAD)/segger

tarball:
	make -C seggerx/Segger clean
	tar -cHf  seggerx.tar --exclude=".*" --exclude=tutorials seggerx
	gzip seggerx.tar
	mv seggerx.tar.gz seggerx_$(shell date +"%Y_%m_%d").tar.gz

build: seggerx
	$(MAKE) -C seggerx/Segger build

sync: seggerx
	$(MAKE) -C seggerx/Segger sync

test: seggerx
	$(MAKE) -C seggerx/Segger test

clean:
	rm -rf seggerx $(SEGGER_SRC)
