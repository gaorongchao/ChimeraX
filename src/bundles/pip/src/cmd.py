# vim: set expandtab shiftwidth=4 softtabstop=4:
# === UCSF ChimeraX Copyright ===
# Copyright 2021 Regents of the University of California.
# All rights reserved.  This software provided pursuant to a
# license agreement containing restrictions on its disclosure,
# duplication and use.  For details see:
# http://www.rbvi.ucsf.edu/chimerax/docs/licensing.html
# This notice must be embedded in or attached to all copies,
# including partial copies, of the software or any revisions
# or derivations thereof.
# === UCSF ChimeraX Copyright ===
import subprocess
import sys

from packaging.requirements import Requirement, InvalidRequirement
from chimerax.core.session import Session
from chimerax.core.commands import BoolArg, StringArg, CmdDesc
from chimerax.core.errors import UserError

__all__ = ['pip', 'pip_desc']

def pip(session: Session, action: str = None, package: str = None, upgrade: bool = False, verbose: bool = False):
    pip_cmd = [sys.executable, "-m", "pip"]
    if action == 'install':
        if not package:
            raise UserError("Can't possibly install an unspecified package.")
        else:
            try:
                req = Requirement(package)
            except InvalidRequirement:
                raise UserError("Can't install package: invalid requirement specified.")
            else:
                pip_cmd.extend(["install", "--user"])
                if upgrade:
                    pip_cmd.extend(["--upgrade"])
                pip_cmd.extend(["%s" % package])
                pip_cmd.extend(["--no-warn-script-location"])
    elif action == 'uninstall':
        if not package:
            raise UserError("Can't possibly uninstall an unspecified package.")
        else:
            if package.lower().startswith("chimerax"):
                raise UserError("Uninstalling this package could compromise ChimeraX; refusing to execute.")
            else:
                pip_cmd.extend(["uninstall", "-y", "%s" % package])
    elif action == 'list':
        pip_cmd.extend(["list"])
    elif action == 'check':
        pip_cmd.extend(["check"])
    elif action == 'show':
        if not package:
            raise UserError("Can't possibly show an unspecified package.")
        pip_cmd.extend(["show", "%s" % package])
    elif action == 'search':
        if not package:
            raise UserError("Can't possibly search for an unspecified package.")
        pip_cmd.extend(["search", "%s" % package])
    elif action == 'debug':
       pip_cmd.extend(["debug"])
    else:
        raise UserError("Unsupported action. Please use one of [install, uninstall, list, check, show, search, debug].")
    if verbose:
        pip_cmd.extend(["--verbose"])
    res = subprocess.run(pip_cmd, capture_output=True)
    session.logger.info(res.stdout.decode('utf-8'))
    session.logger.info(res.stderr.decode('utf-8'))

pip_desc = CmdDesc(
    required=[
        ("action", StringArg)
    ],
    optional=[
        ("package", StringArg)
    ],
    keyword=[
        ("upgrade", BoolArg)
        , ("verbose", BoolArg)
    ],
    synopsis="Call pip from within ChimeraX"
)
