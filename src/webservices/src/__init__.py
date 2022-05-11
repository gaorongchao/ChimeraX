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
from .cxservices_job import CxServicesJob

class _MyAPI(BundleAPI):
	
    api_version = 1

    @staticmethod
    def register_command(bi, ci, logger):
        command_name = ci.name
        logger.info(command_name)
        from . import cmd
        function_name = command_name.replace(' ', '_')
        logger.info(function_name)
        func = getattr(cmd, function_name)
        desc = getattr(cmd, function_name + "_desc")
        if desc.synopsis is None:
            desc.synopsis = ci.synopsis
        from chimerax.core.commands import register
        register(command_name, desc, func, logger=logger)

bundle_api = _MyAPI()
