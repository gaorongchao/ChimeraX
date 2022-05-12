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

# Makefile for user guide
#
TOP	= ../../..
include $(TOP)/mk/config.make

DOCDIR = $(app_datadir)/docs/user/tools

SRCS = $(wildcard *.html)
IMAGES = $(wildcard *.png)

MOUSEICONS = $(TOP)/src/mouse_modes/src/icons/*.png \
		$(TOP)/src/bond_rot/src/bondrot.png \
		$(TOP)/src/struct_measure/src/distance.png \
		$(TOP)/src/label/src/label.png \
		$(TOP)/src/color_key/src/icons/ckiconvertical.png \
		$(TOP)/src/label/src/movelabel.png \
		$(TOP)/src/map/src/icons/*.png \
		$(TOP)/src/map_series/src/vseries.png \
		$(TOP)/src/markers/src/icons/*.png \
		$(TOP)/src/std_commands/src/coordset.png \
		$(TOP)/src/swapaa/src/swapaa.png \
		$(TOP)/src/tug/src/minimize.png \
		$(TOP)/src/tug/src/tug.png \
		$(TOP)/src/zone/src/zone.png \
		$(TOP)/src/pick_blobs/src/pickblobs.png \
		$(TOP)/src/map_eraser/src/eraser.png \
		$(TOP)/src/tape_measure/src/tape.png \
		$(TOP)/src/viewdockx/src/nextdocking.png
MICONDIR = $(DOCDIR)/mouse-icons
SHORTCUTICONS = $(TOP)/src/shortcuts/src/icons/*.png
SICONDIR = $(DOCDIR)/shortcut-icons
TOOLBARICONS = $(TOP)/src/toolbar/src/icons/*.png \
		$(TOP)/src/medical_toolbar/src/icons/opendicom.png \
		$(TOP)/src/sel_inspector/src/icons/magnifying-glass.png
TICONDIR = $(DOCDIR)/toolbar-icons
NUCICONS = $(TOP)/src/nucleotides/src/icons/*.png
NICONDIR = $(DOCDIR)/nuc-icons
BASICICONS = $(TOP)/src/basic_actions/src/lib/*.svg
BICONDIR = $(DOCDIR)/basic-icons
UIICONS = $(TOP)/src/ui/src/icons/*.png
UICONDIR = $(DOCDIR)/ui-icons

install: install-icons
	if [ ! -d "$(DOCDIR)" ]; then mkdir -p $(DOCDIR); fi
	$(RSYNC) $(SRCS) $(IMAGES) $(DOCDIR)

install-icons:
	if [ ! -d "$(MICONDIR)" ]; then mkdir -p $(MICONDIR); fi
	$(RSYNC) $(MOUSEICONS) $(MICONDIR)
	if [ ! -d "$(SICONDIR)" ]; then mkdir -p $(SICONDIR); fi
	$(RSYNC) $(SHORTCUTICONS) $(SICONDIR)
	if [ ! -d "$(TICONDIR)" ]; then mkdir -p $(TICONDIR); fi
	$(RSYNC) $(TOOLBARICONS) $(TICONDIR)
	if [ ! -d "$(NICONDIR)" ]; then mkdir -p $(NICONDIR); fi
	$(RSYNC) $(NUCICONS) $(NICONDIR)
	if [ ! -d "$(BICONDIR)" ]; then mkdir -p $(BICONDIR); fi
	$(RSYNC) $(BASICICONS) $(BICONDIR)
	if [ ! -d "$(UICONDIR)" ]; then mkdir -p $(UICONDIR); fi
	$(RSYNC) $(UIICONS) $(UICONDIR)

clean:
