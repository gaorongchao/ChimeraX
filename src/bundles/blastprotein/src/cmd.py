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

from chimerax.core.commands import CmdDesc, AtomSpecArg
from chimerax.core.commands import StringArg, BoolArg, FloatArg, IntArg, EnumOf

DBs = ["pdb", "nr"]
Matrices = ["BLOSUM45", "BLOSUM62", "BLOSUM80", "BLOSUM90", "BLOSUM100",
            "PAM30", "PAM70"]

def blastprotein(session, atoms=None, database="pdb", cutoff=1.0e-3,
                 matrix="BLOSUM62", max_hits=500, log=None, *, tool_id=None):
    from .job import BlastProteinJob
    if atoms is None:
        atoms = atomspec.everything(session)
    results = atoms.evaluate(session)
    chains = results.atoms.residues.unique_chains
    if len(chains) == 0:
        from chimerax.core.errors import UserError
        raise UserError("no chain was specified")
    elif len(chains) > 1:
        from chimerax.core.errors import UserError
        raise UserError("please choose exactly one chain (%d were specified)" %
                        len(chains))
    chain = chains[0]
    chain_spec = chain.atomspec
    if chain_spec[0] == '/':
        # Make sure we have a structure spec in there so
        # the atomspec remains unique when we load structures later
        chain_spec = chain.structure.atomspec + chain_spec
    if tool_id is None:
        tool = None
    else:
        tool = session.tools.find_by_id(tool_id)
    BlastProteinJob(session, chains[0].characters, chain_spec,
                    database, cutoff, matrix, max_hits, log, tool)
blastprotein_desc = CmdDesc(required=[("atoms", AtomSpecArg),],
                        keyword=[("database", EnumOf(DBs)),
                                 ("cutoff", FloatArg),
                                 ("matrix", EnumOf(Matrices)),
                                 ("max_hits", IntArg),
                                 ("log", BoolArg),
                                 ("tool_id", IntArg),
                                 ],
                        synopsis="Search PDB/NR using BLAST")

def ccd(session, name):
    from .job import CCDJob
    CCDJob(session, name)
ccd_desc = CmdDesc(required=[("name", StringArg),],
                   synopsis="Get Chemical Component Dictionary template")
