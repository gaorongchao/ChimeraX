# -----------------------------------------------------------------------------
# Simulate an electron density map for an atomic model at a specfied
# resolution.  The simulated map is useful for fitting the model into
# an experimental map using correlation coefficient as a goodness of fit.
#
def molmap_command(cmdname, args):

    from .commands import atoms_arg, float_arg, string_arg, openstate_arg
    from .commands import model_id_arg, bool_arg, parse_arguments
    req_args = (('atoms', atoms_arg),
                ('resolution', float_arg))
    opt_args = ()
    kw_args = (('gridSpacing', float_arg),
               ('edgePadding', float_arg),
               ('cutoffRange', float_arg),
               ('sigmaFactor', float_arg),
               ('symmetry', string_arg),
               ('center', string_arg),
               ('axis', string_arg),
               ('coordinateSystem', openstate_arg),
               ('displayThreshold', float_arg),
               ('modelId', model_id_arg),
               ('replace', bool_arg),
               ('showDialog', bool_arg))

    kw = parse_arguments(cmdname, args, req_args, opt_args, kw_args)
    molecule_map(**kw)

# -----------------------------------------------------------------------------
#
from math import sqrt, pi
def molecule_map(atoms, resolution,
                 gridSpacing = None,    # default is 1/3 resolution
                 edgePadding = None,    # default is 3 times resolution
                 cutoffRange = 5,       # in standard deviations
                 sigmaFactor = 1/(pi*sqrt(2)), # standard deviation / resolution
                 symmetry = None,       # Equivalent to sym group option.
                 center = (0,0,0),      # Center of symmetry.
                 axis = (0,0,1),        # Axis of symmetry.
                 coordinateSystem = None,       # Coordinate system of symmetry.
                 displayThreshold = 0.95, # fraction of total density
                 modelId = None, # integer
                 replace = True,
		 showDialog = True
                 ):

    from .commands import CommandError
    if atoms.count() == 0:
        raise CommandError('No atoms specified')

    for vname in ('resolution', 'gridSpacing', 'edgePadding',
                  'cutoffRange', 'sigmaFactor'):
        value = locals()[vname]
        if not isinstance(value, (float,int,type(None))):
            raise CommandError('%s must be number, got "%s"' % (vname,str(value)))

    if edgePadding is None:
        pad = 3*resolution
    else:
        pad = edgePadding

    if gridSpacing is None:
        step = (1./3) * resolution
    else:
        step = gridSpacing

    csys = None
    if symmetry is None:
        transforms = []
    else:
        from .commands import openstate_arg
        if coordinateSystem:
            csys = openstate_arg(coordinateSystem)
        from .SymmetryCopies.symcmd import parse_symmetry
        transforms, csys = parse_symmetry(symmetry, center, axis, csys,
                                          atoms[0].molecule, 'molmap')

    if not modelId is None:
        from .commands import parse_model_id
        modelId = parse_model_id(modelId)

    v = make_molecule_map(atoms, resolution, step, pad,
                          cutoffRange, sigmaFactor, transforms, csys,
                          displayThreshold, modelId, replace, showDialog)
    return v

# -----------------------------------------------------------------------------
#
def make_molecule_map(atoms, resolution, step, pad, cutoff_range,
                      sigma_factor, transforms, csys,
                      display_threshold, model_id,
                      replace, show_dialog):

    grid, molecules = molecule_grid_data(atoms, resolution, step, pad,
                                         cutoff_range, sigma_factor,
                                         transforms, csys)

    if replace:
        from .VolumeViewer import volume_list
        vlist = [v for v in volume_list()
                 if getattr(v, 'molmap_atoms', None) == atoms]
        from .gui import main_window
        main_window.view.close_models(vlist)

    from .VolumeViewer import volume_from_grid_data
    v = volume_from_grid_data(grid, open_model = False,
                              show_dialog = show_dialog)
    v.initialize_thresholds(mfrac = (display_threshold, 1), replace = True)
    v.show()

    v.molmap_atoms = atoms   # Remember atoms used to calculate volume
    v.molmap_parameters = (resolution, step, pad, cutoff_range, sigma_factor)

    from .gui import main_window
    main_window.view.add_model(v)
    return v

# -----------------------------------------------------------------------------
#
def molecule_grid_data(atoms, resolution, step, pad,
                       cutoff_range, sigma_factor,
                       transforms = [], csys = None):

    xyz = atoms.coordinates()

    # Transform coordinates to local coordinates of the molecule containing
    # the first atom.  This handles multiple unaligned molecules.
#    m0 = atoms[0].molecule
#    xf = m0.openState.xform
#    import matrix as M
#    M.transform_points(xyz, M.xform_matrix(xf.inverse()))
#    if csys:
#        xf.premultiply(csys.xform.inverse())
#    tflist = M.coordinate_transform_list(transforms, M.xform_matrix(xf))
    tflist = transforms

    anum = atoms.element_numbers()

    molecules = atoms.molecules()
    if len(molecules) > 1:
        name = 'map %.3g' % (resolution,)
    else:
        name = '%s map %.3g' % (molecules[0].name, resolution)

    grid = gaussian_grid_data(xyz, anum, resolution, step, pad,
                              cutoff_range, sigma_factor, tflist)
    grid.name = name

    return grid, molecules

# -----------------------------------------------------------------------------
#
def gaussian_grid_data(xyz, weights, resolution, step, pad,
                       cutoff_range, sigma_factor, transforms = []):

    xyz_min, xyz_max = point_bounds(xyz, transforms)

    origin = [x-pad for x in xyz_min]
    sdev = sigma_factor * resolution / step
    from numpy import zeros, float32, empty
    sdevs = zeros((len(xyz),3), float32)
    sdevs[:] = sdev
    from math import pow, pi, ceil
    normalization = pow(2*pi,-1.5)*pow(sdev*step,-3)
    shape = [int(ceil((xyz_max[a] - xyz_min[a] + 2*pad) / step))
             for a in (2,1,0)]
    matrix = zeros(shape, float32)

    xyz_to_ijk_tf = ((1.0/step, 0, 0, -origin[0]/step),
                     (0, 1.0/step, 0, -origin[1]/step),
                     (0, 0, 1.0/step, -origin[2]/step))
    from . import matrix as M
    if len(transforms) == 0:
        transforms = [M.identity_matrix()]
    from ._image3d import sum_of_gaussians
    ijk = empty(xyz.shape, float32)
    for tf in transforms:
        ijk[:] = xyz
        M.transform_points(ijk, M.multiply_matrices(xyz_to_ijk_tf, tf))
        sum_of_gaussians(ijk, weights, sdevs, cutoff_range, matrix)
    matrix *= normalization
    
    from .VolumeData import Array_Grid_Data
    grid = Array_Grid_Data(matrix, origin, (step,step,step))

    return grid

# -----------------------------------------------------------------------------
#
def point_bounds(xyz, transforms = []):

    if transforms:
        from numpy import empty, float32
        xyz0 = empty((len(transforms),3), float32)
        xyz1 = empty((len(transforms),3), float32)
        txyz = empty(xyz.shape, float32)
        from . import matrix as M
        for i, tf in enumerate(transforms):
            txyz[:] = xyz
            M.transform_points(txyz, tf)
            xyz0[i,:], xyz1[i,:] = txyz.min(axis=0), txyz.max(axis=0)
        xyz_min, xyz_max = xyz0.min(axis = 0), xyz1.max(axis = 0)
    else:
        xyz_min, xyz_max = xyz.min(axis=0), xyz.max(axis=0)

    return xyz_min, xyz_max
