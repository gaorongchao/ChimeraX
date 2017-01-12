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

"""
ihm: Integrative Hybrid Model file format support
=================================================
"""
def read_ihm(session, filename, name, *args, load_linked_files = True,
             show_sphere_crosslinks = True, show_atom_crosslinks = False, **kw):
    """Read an integrative hybrid models file creating sphere models and restraint models

    :param filename: either the name of a file or a file-like object

    Extra arguments are ignored.
    """

    if hasattr(filename, 'read'):
        # Got a stream
        stream = filename
        filename = stream.name
        stream.close()

    m = IHMModel(session, filename,
                 load_linked_files = load_linked_files,
                 show_sphere_crosslinks = show_sphere_crosslinks,
                 show_atom_crosslinks = show_atom_crosslinks)

    return [m], m.description

# -----------------------------------------------------------------------------
#
from chimerax.core.models import Model
class IHMModel(Model):
    def __init__(self, session, filename,
                 load_linked_files = True,
                 show_sphere_crosslinks = True,
                 show_atom_crosslinks = False):
    
        self.filename = filename
        from os.path import basename, splitext, dirname
        self.ihm_directory = dirname(filename)
        name = splitext(basename(filename))[0]

        Model.__init__(self, name, session)

        self.tables = self.read_tables(filename)

        # Starting atomic models, including experimental and comparative structures and templates.
        stmodels, seqmodels = self.read_starting_models(load_linked_files)
        self.starting_models = stmodels
        self.sequence_alignment_models = seqmodels

        # Crosslinks
        xlinks, xlmodels = self.read_crosslinks()
        self.crosslink_models = xlinks

        # 2D electron microscopy projections
        self.em2d_models = self.read_2dem_images()

        # Make restraint model groupsy
        rmodels = xlmodels + self.em2d_models
        if rmodels:
            r_group = Model('Restraints', self.session)
            r_group.add(rmodels)
            self.add([r_group])

        # Sphere models, ensemble models, groups
        smodels, emodels, gmodels = self.read_sphere_models()
        self.sphere_models = smodels
        self.ensemble_sphere_models = emodels

        # Add crosslinks to sphere models
        if show_sphere_crosslinks:
            self.create_sphere_model_crosslinks(xlinks, smodels, emodels, xlmodels)
        if show_atom_crosslinks:
            self.create_starting_model_crosslinks(xlinks, stmodels, xlmodels)
    
        # Align starting models to first sphere model
        if smodels:
            align_starting_models_to_spheres(stmodels, smodels[0])
    
        # Ensemble localization
        self.localization_models = lmaps = self.read_localization_maps()
        for gm in gmodels:
            gm.add([lmap for lmap in lmaps if lmap.group_id == gm.group_id])

        # Create results model group
        if gmodels:
            if len(gmodels) == 1:
                gmodels[0].name = 'Result sphere models'
                self.add(gmodels)
            else:
                rs_group = Model('Result sphere models', self.session)
                rs_group.add(gmodels)
                self.add([rs_group])

    def read_tables(self, filename):
        # Read ihm tables
        table_names = ['ihm_struct_assembly',  		# Asym ids, entity ids, and entity names
                       'ihm_model_list',		# Model groups
                       'ihm_sphere_obj_site',		# Bead model for each cluster
                       'ihm_cross_link_restraint',	# Crosslinks
                       'ihm_ensemble_info',		# Names of ensembles, e.g. cluster 1, 2, ...
                       'ihm_gaussian_obj_ensemble',	# Distribution of ensemble models
                       'ihm_ensemble_localization', 	# Distribution of ensemble models
                       'ihm_dataset_other',		# Comparative models, EM data, DOI references
                       'ihm_starting_model_details', 	# Starting models, including compararative model templates
                       ]
        from chimerax.core.atomic import mmcif
        table_list = mmcif.get_mmcif_tables(filename, table_names)
        tables = dict(zip(table_names, table_list))
        return tables

    # -----------------------------------------------------------------------------
    #
    def asym_id_names(self):
        sat = self.tables['ihm_struct_assembly']
        sa_fields = [
            'entity_description',
            'asym_id',
            ]
        sa = sat.fields(sa_fields)
        anames = {asym_id : edesc for edesc, asym_id in sa}
        return anames

    # -----------------------------------------------------------------------------
    #
    def read_starting_models(self, load_linked_files):

        # Read experimental starting models and comparative model templates.
        dataset_asym_ids, xmodels, tmodels, seqmodels = self.read_starting_model_details()

        # Read comparative models
        cmodels = self.read_linked_datasets(dataset_asym_ids) if load_linked_files else []

        # Associate comparative models with sequence alignments.
        if seqmodels:
            assign_comparative_models_to_sequences(cmodels, seqmodels)

        # Group starting models, sequence alignment and templates by asym id.
        models = xmodels + cmodels + seqmodels + tmodels
        if models:
            sm_group = Model('Starting models', self.session)
            sma = {}
            for m in models:
                sma.setdefault(m.asym_id, []).append(m)
            smg = []
            anames = self.asym_id_names()
            for asym_id in sorted(sma.keys()):
                am = sma[asym_id]
                name = '%s %s' % (anames[asym_id], asym_id)
                a_group = Model(name, self.session)
                a_group.add(am)
                smg.append(a_group)
                a_group.color = am[0].single_color	# Group color is first model color
            sm_group.add(smg)
            self.add([sm_group])

        return xmodels+cmodels, seqmodels

    # -----------------------------------------------------------------------------
    #
    def read_starting_model_details(self):
        dataset_asym_ids = {}
        xmodels = []
        tmodels = []
        seqmodels = []

        starting_models = self.tables['ihm_starting_model_details']
        if not starting_models:
            return dataset_asym_ids, xmodels, tmodels, seqmodels

        fields = ['asym_id', 'seq_id_begin', 'seq_id_end', 'starting_model_source',
                  'starting_model_db_name', 'starting_model_db_code',
                  'starting_model_auth_asym_id',
                  'dataset_list_id', 'alignment_file']
        rows = starting_models.fields(fields, allow_missing_fields = True)

        from collections import OrderedDict
        alignments = OrderedDict()  # Sequence alignments for comparative models
        for asym_id, seq_beg, seq_end, source, db_name, db_code, auth_asym_id, did, seqfile in rows:
            # TODO: Probably should require comparative model asym_id to match sphere model asym_id
            #       Currently mediator.cif has auth_asym_id identifying chain in comparative model
            #       Corresponding to sphere model asym_id.  But that won't work if db_name/db_code
            #       is used since then auth_asym_id is the db_asym_id.
            cm_asym_id = auth_asym_id if db_code == '?' else asym_id
            dataset_asym_ids.setdefault(did, set()).add((asym_id, cm_asym_id))
            if (source in ('experimental model', 'comparative model') and
                db_name == 'PDB' and db_code != '?'):
                if source == 'comparative model':
                    # Template for a comparative model.
                    tm = TemplateModel(self.session, db_name, db_code, auth_asym_id)
                    models = [tm]
                    tmodels.extend(models)
                    if seqfile:
                        from os.path import join, isfile
                        p = join(self.ihm_directory, seqfile)
                        if isfile(p):
                            a = (p, asym_id, did)
                            sam = alignments.get(a)
                            if sam is None:
                                # Make sequence alignment model for comparative model
                                alignments[a] = sam = SequenceAlignmentModel(self.session, p, asym_id, did)
                            sam.add_template_model(tm)
                elif source == 'experimental model':
                    from chimerax.core.atomic.mmcif import fetch_mmcif
                    models, msg = fetch_mmcif(self.session, db_code, smart_initial_display = False)
                    name = '%s %s' % (db_code, auth_asym_id)
                    for m in models:
                        keep_one_chain(m, auth_asym_id)
                        m.name = name
                        show_colored_ribbon(m, asym_id)
                    xmodels.extend(models)
                for m in models:
                    m.asym_id = asym_id
                    m.seq_begin, m.seq_end = int(seq_beg), int(seq_end)
                    m.dataset_id = did
                    m.comparative_model = (source == 'comparative model')

        seqmodels = list(alignments.values())
        return dataset_asym_ids, xmodels, tmodels, seqmodels
    
    # -----------------------------------------------------------------------------
    #
    def read_linked_datasets(self, dataset_asym_ids):
        '''Read linked data from ihm_dataset_other table'''
        lmodels = []
        datasets_table = self.tables['ihm_dataset_other']
        if not datasets_table:
            return lmodels
        fields = ['dataset_list_id', 'data_type', 'doi', 'content_filename', 'file']
        rows = datasets_table.fields(fields, allow_missing_fields = True)
        for did, data_type, doi, archive_filename, filename in rows:
            if data_type == 'Comparative model':
                from os.path import basename, join
                fopen = atomic_model_reader(filename)
                afopen = atomic_model_reader(archive_filename)
                if fopen:
                    path = join(self.ihm_directory, filename)
                    name = basename(filename)
                    models, msg = fopen(self.session, path, name, smart_initial_display = False)
                elif afopen:
                    from .doi_fetch import fetch_doi_archive_file
                    file = fetch_doi_archive_file(self.session, doi, archive_filename)
                    name = basename(archive_filename)
                    models, msg = afopen(self.session, file, name, smart_initial_display = False)
                    file.close()
                else:
                    models = []	# Don't know how to read atomic model file
                asym_ids = dataset_asym_ids.get(did, [])
                na = len(asym_ids)
                for asym_id, auth_asym_id in asym_ids:
                    for m in models:
                        if na > 1:
                            m = m.copy()
                            keep_one_chain(m, auth_asym_id)
                            m.name += ' ' + auth_asym_id
                        m.dataset_id = did
                        m.asym_id = asym_id
                        m.comparative_model = True
                        show_colored_ribbon(m, asym_id)
                        lmodels.append(m)
      
        return lmodels

    # -----------------------------------------------------------------------------
    #
    def read_sphere_models(self):
        gmodels = self.make_sphere_model_groups()
        for g in gmodels[1:]:
            g.display = False	# Only show first group.
        self.add(gmodels)

        smodels, emodels = self.make_sphere_models(gmodels)
        return smodels, emodels, gmodels

    # -----------------------------------------------------------------------------
    #
    def make_sphere_model_groups(self):
        mlt = self.tables['ihm_model_list']
        ml_fields = [
            'model_id',
            'model_group_id',
            'model_group_name',]
        ml = mlt.fields(ml_fields)
        gm = {}
        for mid, gid, gname in ml:
            gm.setdefault((gid, gname), []).append(mid)
        models = []
        for (gid, gname), mid_list in gm.items():
            m = Model(gname, self.session)
            m.group_id = gid
            m.ihm_model_ids = mid_list
            models.append(m)
        models.sort(key = lambda m: m.group_id)
        return models

    # -----------------------------------------------------------------------------
    #
    def make_sphere_models(self, group_models):
        mlt = self.tables['ihm_model_list']
        ml_fields = [
            'model_id',
            'model_name',
            'model_group_id',
            'file',]
        ml = mlt.fields(ml_fields, allow_missing_fields = True)
        mnames = {mid:mname for mid,mname,gid,file in ml}

        sost = self.tables['ihm_sphere_obj_site']
        sos_fields = [
            'seq_id_begin',
            'seq_id_end',
            'asym_id',
            'cartn_x',
            'cartn_y',
            'cartn_z',
            'object_radius',
            'model_id']
        spheres = sost.fields(sos_fields)
        mspheres = {}
        for seq_beg, seq_end, asym_id, x, y, z, radius, model_id in spheres:
            sb, se = int(seq_beg), int(seq_end)
            xyz = float(x), float(y), float(z)
            r = float(radius)
            mspheres.setdefault(model_id, []).append((asym_id,sb,se,xyz,r))

        smodels = [SphereModel(self.session, mnames[mid], mid, slist)
                   for mid, slist in mspheres.items()]
        smodels.sort(key = lambda m: m.ihm_model_id)

        # Add sphere models to group
        gmodel = {id:g for g in group_models for id in g.ihm_model_ids}
        for sm in smodels:
            gmodel[sm.ihm_model_id].add([sm])

        # Undisplay all but first sphere model in each group
        gfound = set()
        for sm in smodels:
            g = gmodel[sm.ihm_model_id]
            if g in gfound:
                sm.display = False
            else:
                gfound.add(g)

        # Open ensemble sphere models that are not included in ihm sphere obj table.
        emodels = []
        from os.path import isfile, join
        smids = set(sm.ihm_model_id for sm in smodels)
        for mid, mname, gid, file in ml:
            path = join(self.ihm_directory, file)
            if file and isfile(path) and file.endswith('.pdb') and mid not in smids:
                from chimerax.core.atomic.pdb import open_pdb
                mlist,msg = open_pdb(self.session, path, mname,
                                     smart_initial_display = False, explode = False)
                sm = mlist[0]
                sm.display = False
                sm.ss_assigned = True	# Don't assign secondary structure to sphere model
                atoms = sm.atoms
                from chimerax.core.atomic.colors import chain_colors
                atoms.colors = chain_colors(atoms.residues.chain_ids)
                if isfile(path + '.crd'):
                    from .coordsets import read_coordinate_sets
                    read_coordinate_sets(path + '.crd', sm)
                sm.name += ' %d models' % sm.num_coord_sets
                gmodel[gid].add([sm])
                emodels.append(sm)

        # Copy bead radii from best score model to ensemble models
        if smodels and emodels:
            r = smodels[0].atoms.radii
            for em in emodels:
                em.atoms.radii = r

        return smodels, emodels

    # -----------------------------------------------------------------------------
    #
    def read_crosslinks(self):
        clrt = self.tables['ihm_cross_link_restraint']
        if clrt is None:
            return [], []

        clrt_fields = [
            'asym_id_1',
            'seq_id_1',
            'asym_id_2',
            'seq_id_2',
            'type',
            'distance_threshold'
            ]
        clrt_rows = clrt.fields(clrt_fields)
        xlinks = {}
        for asym_id_1, seq_id_1, asym_id_2, seq_id_2, type, distance_threshold in clrt_rows:
            xl = Crosslink(asym_id_1, int(seq_id_1), asym_id_2, int(seq_id_2),
                           float(distance_threshold))
            xlinks.setdefault(type, []).append(xl)

        xlmodels = [CrossLinkModel(self.session, xltype, len(xllist))
                    for xltype, xllist in xlinks.items()]

        return xlinks, xlmodels

    # -----------------------------------------------------------------------------
    #
    def create_sphere_model_crosslinks(self, xlinks, smodels, emodels, xlmodels):
        xpbgs = []
        # Create cross links for sphere models
        for i,smodel in enumerate(smodels):
            pbgs = make_crosslink_pseudobonds(self.session, xlinks, smodel.residue_sphere,
                                              name = smodel.ihm_model_id,
                                              parent = smodel)
            if i == 0:
                # Show only multi-residue spheres and crosslink end-point spheres
                satoms = smodel.atoms
                satoms.displays = False
                satoms.filter(satoms.residues.names != '1').displays = True
                for pbg in pbgs:
                    a1,a2 = pbg.pseudobonds.atoms
                    a1.displays = True
                    a2.displays = True
            else:
                # Hide crosslinks for all but first sphere model
                for pbg in pbgs:
                    pbg.display = False
            xpbgs.extend(pbgs)

        if emodels and smodels:
            for emodel in emodels:
                pbgs = make_crosslink_pseudobonds(self.session, xlinks,
                                                  ensemble_sphere_lookup(emodel, smodels[0]),
                                                  parent = emodel)
                xpbgs.extend(pbgs)

        for xlm in xlmodels:
            pbgs = [pbg for pbg in xpbgs if pbg.crosslink_type == xlm.crosslink_type]
            xlm.add_pseudobond_models(pbgs)

    # -----------------------------------------------------------------------------
    # Create cross links for starting atomic models.
    #
    def create_starting_model_crosslinks(self, xlinks, amodels, xlmodels):
        if amodels:
            # Starting models may not have disordered regions, so crosslinks will be omitted.
            pbgs = make_crosslink_pseudobonds(self.session, xlinks, atom_lookup(amodels))
            for xlm in xlmodels:
                pbgs = [pbg for pbg in xpbgs if pbg.crosslink_type == xlm.crosslink_type]
                xlm.add_pseudobond_models(pbgs)

    # -----------------------------------------------------------------------------
    #
    def read_2dem_images(self):
        em2d = []
        dot = self.tables['ihm_dataset_other']
        fields = ['data_type', 'file']
        for data_type, filename in dot.fields(fields, allow_missing_fields = True):
            if data_type == '2DEM class average' and filename.endswith('.mrc'):
                from os.path import join, isfile
                image_path = join(self.ihm_directory, filename)
                if isfile(image_path):
                    from chimerax.core.map.volume import open_map
                    maps,msg = open_map(self.session, image_path)
                    v = maps[0]
                    v.name += ' 2D electron microscopy'
                    v.initialize_thresholds(vfrac = (0.01,1), replace = True)
                    v.show()
                    em2d.append(v)
        return em2d

    # -----------------------------------------------------------------------------
    #
    def read_localization_maps(self):

        lmaps = self.read_ensemble_localization_maps()
        if len(lmaps) == 0:
            lmaps = self.read_gaussian_localization_maps()
        if lmaps:
            for g in lmaps[1:]:
                g.display = False	# Only show first ensemble
        return lmaps

    # -----------------------------------------------------------------------------
    #
    def read_ensemble_localization_maps(self, level = 0.2, opacity = 0.5):
        '''Level sets surface threshold so that fraction of mass is outside the surface.'''

        eit = self.tables['ihm_ensemble_info']
        elt = self.tables['ihm_ensemble_localization']
        if eit is None or elt is None:
            return []

        ensemble_fields = ['ensemble_id', 'model_group_id', 'num_ensemble_models']
        ens = eit.fields(ensemble_fields)
        ens_group = {id:(gid,int(n)) for id, gid, n in ens}

        loc_fields = ['asym_id', 'ensemble_id', 'file']
        loc = elt.fields(loc_fields)
        ens = {}
        for asym_id, ensemble_id, file in loc:
            ens.setdefault(ensemble_id, []).append((asym_id, file))

        pmods = []
        from chimerax.core.map.volume import open_map
        from chimerax.core.atomic.colors import chain_rgba
        from os.path import join
        for ensemble_id in sorted(ens.keys()):
            asym_loc = ens[ensemble_id]
            gid, n = ens_group[ensemble_id]
            name = 'Localization map ensemble %s' % ensemble_id
            m = Model(name, self.session)
            m.group_id = gid
            pmods.append(m)
            for asym_id, filename in sorted(asym_loc):
                map_path = join(self.ihm_directory, filename)
                maps,msg = open_map(self.session, map_path, show = False, show_dialog=False)
                color = chain_rgba(asym_id)[:3] + (opacity,)
                v = maps[0]
                ms = v.matrix_value_statistics()
                vlev = ms.mass_rank_data_value(level)
                v.set_parameters(surface_levels = [vlev], surface_colors = [color])
                v.show_in_volume_viewer = False
                v.show()
                m.add([v])

        return pmods

    # -----------------------------------------------------------------------------
    #
    def read_gaussian_localization_maps(self, level = 0.2, opacity = 0.5):
        '''Level sets surface threshold so that fraction of mass is outside the surface.'''

        eit = self.tables['ihm_ensemble_info']
        goet = self.tables['ihm_gaussian_obj_ensemble']
        if eit is None or goet is None:
            return []

        ensemble_fields = ['ensemble_id', 'model_group_id', 'num_ensemble_models']
        ens = eit.fields(ensemble_fields)
        ens_group = {id:(gid,int(n)) for id, gid, n in ens}

        gauss_fields = ['asym_id',
                       'mean_cartn_x',
                       'mean_cartn_y',
                       'mean_cartn_z',
                       'weight',
                       'covariance_matrix[1][1]',
                       'covariance_matrix[1][2]',
                       'covariance_matrix[1][3]',
                       'covariance_matrix[2][1]',
                       'covariance_matrix[2][2]',
                       'covariance_matrix[2][3]',
                       'covariance_matrix[3][1]',
                       'covariance_matrix[3][2]',
                       'covariance_matrix[3][3]',
                       'ensemble_id']
        cov = {}	# Map model_id to dictionary mapping asym id to list of (weight,center,covariance) triples
        gauss_rows = goet.fields(gauss_fields)
        from numpy import array, float64
        for asym_id, x, y, z, w, c11, c12, c13, c21, c22, c23, c31, c32, c33, eid in gauss_rows:
            center = array((float(x), float(y), float(z)), float64)
            weight = float(w)
            covar = array(((float(c11),float(c12),float(c13)),
                           (float(c21),float(c22),float(c23)),
                           (float(c31),float(c32),float(c33))), float64)
            cov.setdefault(eid, {}).setdefault(asym_id, []).append((weight, center, covar))

        # Compute probability volume models
        pmods = []
        from chimerax.core.map import volume_from_grid_data
        from chimerax.core.atomic.colors import chain_rgba

        for ensemble_id in sorted(cov.keys()):
            asym_gaussians = cov[ensemble_id]
            gid, n = ens_group[ensemble_id]
            m = Model('Localization map ensemble %s of %d models' % (ensemble_id, n), self.session)
            m.group_id = gid
            pmods.append(m)
            for asym_id in sorted(asym_gaussians.keys()):
                g = probability_grid(asym_gaussians[asym_id])
                g.name = '%s Gaussians' % asym_id
                g.rgba = chain_rgba(asym_id)[:3] + (opacity,)
                v = volume_from_grid_data(g, self.session, show_data = False,
                                          open_model = False, show_dialog = False)
                v.initialize_thresholds()
                ms = v.matrix_value_statistics()
                vlev = ms.mass_rank_data_value(level)
                v.set_parameters(surface_levels = [vlev])
                v.show_in_volume_viewer = False
                v.show()
                m.add([v])

        return pmods

    # -----------------------------------------------------------------------------
    #
    @property
    def description(self):
        # Report what was read in
        nc = len([m for m in self.starting_models if m.comparative_model])
        nx = len([m for m in self.starting_models if not m.comparative_model])
        nsa = len(self.sequence_alignment_models)
        nt = sum([len(sqm.template_models) for sqm in self.sequence_alignment_models], 0)
        nem = len(self.em2d_models)
        ns = len(self.sphere_models)
        nse = len(self.ensemble_sphere_models)
        nl = sum([len(lm.child_models()) for lm in self.localization_models], 0)
        xldesc = ', '.join('%d %s crosslinks' % (len(xls),type)
                           for type,xls in self.crosslink_models.items())
        esizes = ' and '.join('%d'%em.num_coord_sets for em in self.ensemble_sphere_models)
        msg = ('Opened IHM file %s\n'
               ' %d xray/nmr models, %d comparative models, %d sequence alignments, %d templates\n'
               ' %s, %d 2D electron microscopy images\n'
               ' %d sphere models, %d ensembles with %s models, %d localization maps' %
               (self.filename, nx, nc, nsa, nt, xldesc, nem, ns, nse, esizes, nl))
        return msg

# -----------------------------------------------------------------------------
#
class Crosslink:
    def __init__(self, asym1, seq1, asym2, seq2, dist):
        self.asym1 = asym1
        self.seq1 = seq1
        self.asym2 = asym2
        self.seq2 = seq2
        self.distance = dist

# -----------------------------------------------------------------------------
# Crosslink model controls display of pseudobond groups but does not display
# anything itself.  The controlled pseudobond groups are not generally child models.
#
class CrossLinkModel(Model):
    def __init__(self, session, crosslink_type, count):
        name = '%d %s crosslinks' % (count, crosslink_type)
        Model.__init__(self, name, session)
        self.crosslink_type = crosslink_type
        self._pseudobond_groups = []

    def add_pseudobond_models(self, pbgs):
        self._pseudobond_groups.extend(pbgs)
        
    def _get_display(self):
        for pbg in self._pseudobond_groups:
            if pbg.display:
                return True
        return False
    def _set_display(self, display):
        for pbg in self._pseudobond_groups:
            pbg.display = display
    display = property(_get_display, _set_display)

# -----------------------------------------------------------------------------
#
def make_crosslink_pseudobonds(session, xlinks, atom_lookup,
                               name = None,
                               parent = None,
                               radius = 1.0,
                               color = (0,255,0,255),		# Green
                               long_color = (255,0,0,255)):	# Red
    
    pbgs = []
    new_pbgroup = session.pb_manager.get_group if parent is None else parent.pseudobond_group
    for type, xlist in xlinks.items():
        xname = '%d %s crosslinks' % (len(xlist), type)
        if name is not None:
            xname += ' ' + name
        g = new_pbgroup(xname)
        g.crosslink_type = type
        pbgs.append(g)
        missing = []
        apairs = {}
        for xl in xlist:
            a1 = atom_lookup(xl.asym1, xl.seq1)
            a2 = atom_lookup(xl.asym2, xl.seq2)
            if (a1,a2) in apairs or (a2,a1) in apairs:
                # Crosslink already created between multiresidue beads
                continue
            if a1 and a2 and a1 is not a2:
                b = g.new_pseudobond(a1, a2)
                b.color = long_color if b.length > xl.distance else color
                b.radius = radius
                b.halfbond = False
                b.restraint_distance = xl.distance
            elif a1 is None:
                missing.append((xl.asym1, xl.seq1))
            elif a2 is None:
                missing.append((xl.asym2, xl.seq2))
        if missing:
            session.logger.info('Missing %d crosslink residues %s'
                                % (len(missing), ','.join('/%s:%d' for asym_id, seq_num in missing)))
                
    return pbgs

# -----------------------------------------------------------------------------
#
def probability_grid(wcc, voxel_size = 5, cutoff_sigmas = 3):
    # Find bounding box for probability distribution
    from chimerax.core.geometry import Bounds, union_bounds
    from math import sqrt, ceil
    bounds = []
    for weight, center, covar in wcc:
        sigmas = [sqrt(covar[a,a]) for a in range(3)]
        xyz_min = [x-s for x,s in zip(center,sigmas)]
        xyz_max = [x+s for x,s in zip(center,sigmas)]
        bounds.append(Bounds(xyz_min, xyz_max))
    b = union_bounds(bounds)
    isize,jsize,ksize = [int(ceil(s  / voxel_size)) for s in b.size()]
    from numpy import zeros, float32, array
    a = zeros((ksize,jsize,isize), float32)
    xyz0 = b.xyz_min
    vsize = array((voxel_size, voxel_size, voxel_size), float32)

    # Add Gaussians to probability distribution
    for weight, center, covar in wcc:
        acenter = (center - xyz0) / vsize
        cov = covar.copy()
        cov *= 1/(voxel_size*voxel_size)
        add_gaussian(weight, acenter, cov, a)

    from chimerax.core.map.data import Array_Grid_Data
    g = Array_Grid_Data(a, origin = xyz0, step = vsize)
    return g

# -----------------------------------------------------------------------------
#
def add_gaussian(weight, center, covar, array):

    from numpy import linalg
    cinv = linalg.inv(covar)
    d = linalg.det(covar)
    from math import pow, sqrt, pi
    s = weight * pow(2*pi, -1.5) / sqrt(d)	# Normalization to sum 1.
    covariance_sum(cinv, center, s, array)

# -----------------------------------------------------------------------------
#
def covariance_sum(cinv, center, s, array):
    from numpy import dot
    from math import exp
    ksize, jsize, isize = array.shape
    i0,j0,k0 = center
    for k in range(ksize):
        for j in range(jsize):
            for i in range(isize):
                v = (i-i0, j-j0, k-k0)
                array[k,j,i] += s*exp(-0.5*dot(v, dot(cinv, v)))

from chimerax.core.map import covariance_sum
        
# -----------------------------------------------------------------------------
#
class TemplateModel(Model):
    def __init__(self, session, db_name, db_code, db_asym_id):
        name = 'Template %s %s' % (db_code, db_asym_id)
        Model.__init__(self, name, session)
        self.db_name = db_name
        self.db_code = db_code
        self.db_asym_id = db_asym_id
        self.sequence_alignment_model = None
        
    def _get_display(self):
        return False
    def _set_display(self, display):
        if display:
            self.fetch_model()
    display = property(_get_display, _set_display)

    def fetch_model(self):
        if self.db_name != 'PDB' or len(self.db_code) != 4:
            return

        from chimerax.core.atomic.mmcif import fetch_mmcif
        models, msg = fetch_mmcif(self.session, self.db_code, smart_initial_display = False)
        name = '%s %s' % (self.db_code, self.db_asym_id)
        for i,m in enumerate(models):
            m.name = self.name
            m.pdb_id = self.db_code
            m.pdb_chain_id = self.db_asym_id
            m.asym_id = self.asym_id
            m.dataset_id = self.dataset_id	# For locating comparative model
            keep_one_chain(m, self.db_asym_id)
            show_colored_ribbon(m, self.asym_id, color_offset = 80)
            if i == 0:
                m.id = self.id

        # Replace TemplateModel with AtomicStructure
        p = self.parent
        self.session.models.remove([self])
        p.add(models)

        sam = self.sequence_alignment_model
        sam.associate_structures(models)
        sam.align_structures(models)
        
# -----------------------------------------------------------------------------
#
class SequenceAlignmentModel(Model):
    def __init__(self, session, alignment_file, asym_id, dataset_id):
        self.alignment_file = alignment_file
        self.asym_id = asym_id			# Identifies comparative model
        self.dataset_id = dataset_id		# Identifies comparative model
        self.template_models = []		# Filled in after templates fetched.
        self.comparative_model = None
        self.alignment = None
        from os.path import basename
        Model.__init__(self, 'Alignment ' + basename(alignment_file), session)
        self.display = False

    def add_template_model(self, model):
        self.template_models.append(model)
        model.sequence_alignment_model = self
        
    def _get_display(self):
        a = self.alignment
        if a is not None:
            for v in a.viewers:
                if v.displayed():
                    return True
        return False
    def _set_display(self, display):
        a = self.alignment
        if display:
            self.show_alignment()
        elif a:
            for v in a.viewers:
                v.display(False)
    display = property(_get_display, _set_display)

    def show_alignment(self):
        a = self.alignment
        if a is None:
            from chimerax.seqalign.parse import open_file
            a = open_file(self.session, None, self.alignment_file,
                          auto_associate=False, return_vals='alignments')[0]
            self.alignment = a
            self.associate_structures(self.template_models)
            cm = self.comparative_model
            if cm:
                a.associate(cm.chains[0], a.seqs[-1], force = True)
        else:
            for v in a.viewers:
                v.display(True)
        return a

    def associate_structures(self, models):
        # Associate templates with sequences in alignment.
        a = self.alignment
        if a is None:
            a = self.show_alignment()
        from chimerax.core.atomic import AtomicStructure
        tmap = {'%s%s' % (tm.pdb_id.lower(), tm.pdb_chain_id) : tm
                for tm in models if isinstance(tm, AtomicStructure)}
        if tmap:
            for seq in a.seqs:
                tm = tmap.get(seq.name)
                if tm:
                    a.associate(tm.chains[0], seq, force = True)
                    tm._associated_sequence = seq

    def align_structures(self, models):
        a = self.alignment
        if a is None:
            a = self.show_alignment()
        cm = self.comparative_model
        if a and cm:
            for m in models:
                if m._associated_sequence:
                    results = a.match(cm.chains[0], [m.chains[0]], iterate=None)
                    if results:
                        # Show only matched residues
                        # TODO: Might show full interval of residues with unused
                        #       insertions colored gray
                        matoms = results[0][0]
                        m.residues.ribbon_displays = False
                        matoms.unique_residues.ribbon_displays = True
                
# -----------------------------------------------------------------------------
#
def atomic_model_reader(filename):
    if filename.endswith('.cif'):
        from chimerax.core.atomic.mmcif import open_mmcif
        return open_mmcif
    elif filename.endswith('.pdb'):
        from chimerax.core.atomic.pdb import open_pdb
        return open_pdb
    return None
                
# -----------------------------------------------------------------------------
#
def assign_comparative_models_to_sequences(cmodels, seqmodels):
    cmap = {(cm.dataset_id, cm.asym_id):cm for cm in cmodels}
    for sam in seqmodels:
        ckey = (sam.dataset_id, sam.asym_id)
        if ckey in cmap:
            sam.comparative_model = cmap[ckey]
    
# -----------------------------------------------------------------------------
#
def keep_one_chain(s, chain_id):
    atoms = s.atoms
    cids = atoms.residues.chain_ids
    dmask = (cids != chain_id)
    dcount = dmask.sum()
    if dcount > 0 and dcount < len(atoms):	# Don't delete all atoms if chain id not found.
        datoms = atoms.filter(dmask)
        datoms.delete()
    elif dcount == len(atoms):
        print ('No chain %s in %s' % (chain_id, s.name))

# -----------------------------------------------------------------------------
#
def group_template_models(session, template_models, seq_alignment_models, sa_group):
    '''Place template models in groups under their sequence alignment model.'''
    for sam in seq_alignment_models:
        sam.add(sam.template_models)
    tmodels = [tm for tm in template_models if tm.sequence_alignment_model is None]
    if tmodels:
        et_group = Model('extra templates', session)
        et_group.add(tmodels)
        sa_group.add(et_group)

# -----------------------------------------------------------------------------
#
def align_template_models(session, comparative_models):
    for cm in comparative_models:
        tmodels = getattr(cm, 'template_models', [])
        if tmodels is None:
            continue
        catoms = cm.atoms
        rnums = catoms.residues.numbers
        for tm in tmodels:
            # Find range of comparative model residues that template was matched to.
            from numpy import logical_and
            cratoms = catoms.filter(logical_and(rnums >= tm.seq_begin, rnums <= tm.seq_end))
            print('match maker', tm.name, 'to', cm.name, 'residues', tm.seq_begin, '-', tm.seq_end)
            from chimerax.match_maker.match import cmd_match
            matches = cmd_match(session, tm.atoms, cratoms, iterate = False)
            fatoms, toatoms, rmsd, full_rmsd, tf = matches[0]
            # Color unmatched template residues gray.
            mres = fatoms.residues
            tres = tm.residues
            nonmatched_res = tres.subtract(mres)
            nonmatched_res.ribbon_colors = (170,170,170,255)
            # Hide unmatched template beyond ends of matching residues
            mnums = mres.numbers
            tnums = tres.numbers
            tres.filter(tnums < mnums.min()).ribbon_displays = False
            tres.filter(tnums > mnums.max()).ribbon_displays = False

# -----------------------------------------------------------------------------
#
def show_colored_ribbon(m, asym_id, color_offset = None):
    if asym_id is None:
        from numpy import random, uint8
        color = random.randint(128,255,(4,),uint8)
        color[3] = 255
    else:
        from chimerax.core.atomic.colors import chain_rgba8
        color = chain_rgba8(asym_id)
        if color_offset:
            from numpy.random import randint
            offset = randint(-color_offset,color_offset,(3,))
            for a in range(3):
                color[a] = max(0, min(255, color[a] + offset[a]))
    r = m.residues
    r.ribbon_colors = color
    r.ribbon_displays = True
    a = m.atoms
    a.colors = color
    a.displays = False

# -----------------------------------------------------------------------------
#
def align_starting_models_to_spheres(amodels, smodel):
    if len(amodels) == 0:
        return
    for m in amodels:
        # Align comparative model residue centers to sphere centers
        res = m.residues
        rnums = res.numbers
        rc = res.centers
        mxyz = []
        sxyz = []
        for rn, c in zip(rnums, rc):
            s = smodel.residue_sphere(m.asym_id, rn)
            if s:
                mxyz.append(c)
                sxyz.append(s.coord)
                # TODO: For spheres with multiple residues use average residue center
        if len(mxyz) >= 3:
            from chimerax.core.geometry import align_points
            from numpy import array, float64
            p, rms = align_points(array(mxyz,float64), array(sxyz,float64))
            m.position = p
            print ('aligned %s, %d residues, rms %.4g' % (m.name, len(mxyz), rms))
        else:
            print ('could not align aligned %s to spheres, %d matching residues' % (m.name, len(mxyz)))
            
# -----------------------------------------------------------------------------
#
def atom_lookup(models):
    amap = {}
    for m in models:
        res = m.residues
        for res_num, atom in zip(res.numbers, res.principal_atoms):
            amap[(m.asym_id, res_num)] = atom
    def lookup(asym_id, res_num, amap=amap):
        return amap.get((asym_id, res_num))
    return lookup
    
# -----------------------------------------------------------------------------
#
def ensemble_sphere_lookup(emodel, smodel):
    def lookup(asym_id, res_num, atoms=emodel.atoms, smodel=smodel):
        a = smodel.residue_sphere(asym_id, res_num)
        return None if a is None else atoms[a.coord_index]
    return lookup

# -----------------------------------------------------------------------------
#
from chimerax.core.atomic import Structure
class SphereModel(Structure):
    def __init__(self, session, name, ihm_model_id, sphere_list):
        Structure.__init__(self, session, name = name, smart_initial_display = False)
        self.ihm_model_id = ihm_model_id
        self._asym_models = {}
        self._sphere_atom = sa = {}	# (asym_id, res_num) -> sphere atom
        
        from chimerax.core.atomic.colors import chain_rgba8
        for (asym_id, sb,se,xyz,r) in sphere_list:
            aname = 'CA'
            a = self.new_atom(aname, 'C')
            a.coord = xyz
            a.radius = r
            a.draw_mode = a.SPHERE_STYLE
            a.color = chain_rgba8(asym_id)
            rname = '%d' % (se-sb+1)
            # Convention on ensemble PDB files is beads get middle residue number of range
            rnum = sb + (sb-se+1)//2
            r = self.new_residue(rname, asym_id, rnum)
            r.add_atom(a)
            for s in range(sb, se+1):
                sa[(asym_id,s)] = a
        self.new_atoms()

    def residue_sphere(self, asym_id, res_num):
        return self._sphere_atom.get((asym_id,res_num))
