# vim: set expandtab shiftwidth=4 softtabstop=4:

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

from chimerax.core.toolshed import BundleAPI

class _ImageFormatsBundleAPI(BundleAPI):
    
    @staticmethod
    def run_provider(session, name, mgr):
        from chimerax.save import SaverInfo
        class ImageInfo(SaverInfo):
            def save(self, session, path, format_name=name, **kw):
                from .save import save_image
                save_image(session, path, format_name, **kw)

            @property
            def save_args(self):
                from chimerax.core.commands import PositiveIntArg, FloatArg, BoolArg, Bounded, IntArg
                return {
                    'height': PositiveIntArg,
                    'pixel_size': FloatArg,
                    'quality': Bounded(IntArg, min=0, max=100),
                    'supersample': PositiveIntArg,
                    'transparent_background': BoolArg,
                    'width': PositiveIntArg,
                }
        return ImageInfo()

bundle_api = _ImageFormatsBundleAPI()
