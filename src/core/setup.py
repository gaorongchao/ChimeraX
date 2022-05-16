
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

# import distutils.core, distutils.debug
# distutils.core.DEBUG = True
# distutils.debug.DEBUG = True

from setuptools import setup, Extension
from Cython.Build import cythonize 

import glob
import os
import sys

shlib_dir = "SHLIB_DIR"
pkg_dir = "PKG_DIR"
data_dir = "DATA_DIR"
if sys.platform.startswith('win'):
    # data files are relative to bindir
    rel_inst_shlib_dir = "" 
else:
    # data files are relative to rootdir
    rel_inst_shlib_dir = os.path.basename(shlib_dir)

cythonize(Extension("chimerax.core._serialize", sources=["src/_serialize.pyx"]))

setup(
    ext_modules = [
        Extension("chimerax.core._mac_util", sources=glob.glob("src/mac_util_cpp/*[!.h]"))
        , Extension("chimerax.core._serialize", sources=["src/_serialize.cpp"])
    ]
)
