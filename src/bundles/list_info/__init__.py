# vim: set expandtab shiftwidth=4 softtabstop=4:

from chimerax.core.toolshed import BundleAPI

class _InfoAPI(BundleAPI):

    @staticmethod
    def register_command(command_name, logger):
        # 'register_command' is lazily called when the command is referenced
        from . import cmd
        from chimerax.core.commands import register, create_alias
        register('info',
                 cmd.info_desc,
                 cmd.info, logger=logger)
        create_alias("listinfo", "info $*", logger=logger)
        register("info bounds",
                 cmd.info_bounds_desc,
                 cmd.info_bounds, logger=logger)
        register("info models",
                 cmd.info_models_desc,
                 cmd.info_models, logger=logger)
        register("info chains",
                 cmd.info_chains_desc,
                 cmd.info_chains, logger=logger)
        register("info polymers",
                 cmd.info_polymers_desc,
                 cmd.info_polymers, logger=logger)
        register("info residues",
                 cmd.info_residues_desc,
                 cmd.info_residues, logger=logger)
        register("info atoms",
                 cmd.info_atoms_desc,
                 cmd.info_atoms, logger=logger)
        register("info selection",
                 cmd.info_selection_desc,
                 cmd.info_selection, logger=logger)
        register("info resattr",
                 cmd.info_resattr_desc,
                 cmd.info_resattr, logger=logger)
        register("info distmat",
                 cmd.info_distmat_desc,
                 cmd.info_distmat, logger=logger)
        register("info notify start",
                 cmd.info_notify_start_desc,
                 cmd.info_notify_start, logger=logger)
        register("info notify stop",
                 cmd.info_notify_stop_desc,
                 cmd.info_notify_stop, logger=logger)
        register("info notify suspend",
                 cmd.info_notify_suspend_desc,
                 cmd.info_notify_suspend, logger=logger)
        register("info notify resume",
                 cmd.info_notify_resume_desc,
                 cmd.info_notify_resume, logger=logger)

bundle_api = _InfoAPI()
