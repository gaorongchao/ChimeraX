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

def register_core_commands(session):
    """Register core commands"""
    from importlib import import_module
    # Remember that the order is important, when a command name is
    # abbreviated, the first one registered that matches wins, not
    # the first in alphabetical order.
    modules = [
        'alias', 'align',
        'camera', 'cartoon', 'cd', 'clip', 'close', 'cofr', 'color', 'colorname',
        'coordset', 'crossfade',
        'delete', 'devel', 'distance', 'dssp', 'exit', 'graphics', 'hide',
        'lighting', 'material',
        'measure_convexity', 'measure_buriedarea', 'measure_length',
        'measure_sasa',
        'mousemode', 'move',
        'open', 'palette', 'pdbimages', 'perframe', 'pwd',
        'rainbow', 'rename', 'roll', 'run', 'rungs', 'runscript',
        'save', 'select', 'set', 'setattr', 'show', 'size', 'split',
        'stop', 'style', 'surface', 'sym',
        'time', 'toolshed', 'transparency', 'turn', 'undo',
        'usage', 'view', 'version', 'wait', 'windowsize', 'zoom'
    ]
    for mod in modules:
        m = import_module(".%s" % mod, __package__)
        m.register_command(session)
