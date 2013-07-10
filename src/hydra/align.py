def align(atoms, ref_atoms, move = None, each = None, same = None, report_matrix=False):
    """Move atoms to minimize RMSD with ref_atoms.

    If 'move' is 'molecules', superimpose the models.  If it is 'atoms',
    'residues' or 'chains' move just those atoms.  If move is False
    move nothing or True move molecules.  If move is a tuple, list or
    set of atoms then move those.

    If 'each' is "molecule" then each molecule of atoms is separately
    aligned to the ref_atoms.  If 'each' is "chain" then each chain is
    aligned separately.  Default is that all atoms are aligned as one group.

    If 'same' is 'n' then only atoms with matching residue numbers are paired.
    It is assumed the atoms are in residue number order.  Unpaired atoms or ref_atoms
    are not used.
    
    If 'report_matrix' is True, report the transformation matrix to
    the Reply Log.
    """

    if each == 'chain':
        groups = atoms.separate_chains()
        if move is None:
            move = 'chains'
        for gatoms in groups:
            align(gatoms, ref_atoms, move=move, same=same, report_matrix=report_matrix)
        return
    elif each == 'molecule':
        groups = atoms.separate_molecules()
        for gatoms in groups:
            align(gatoms, ref_atoms, move=move, same=same, report_matrix=report_matrix)
        return

    if same == 'n':
        patoms, pref_atoms = paired_atoms(atoms, ref_atoms)
        da, dra = atoms.count() - patoms.count(), ref_atoms.count() - pref_atoms.count()
        if da > 0 or dra > 0:
            from .gui import log_message
            log_message('Pairing dropped %d atoms and %d reference atoms' % (da, dra))
        print ('p', patoms.count(), atoms.count(), pref_atoms.count(), ref_atoms.count())
        print ('m', [m.id for m in atoms.molecules()], [m.id for m in ref_atoms.molecules()])
        atoms, ref_atoms = patoms, pref_atoms

    if atoms.count() != ref_atoms.count():
        from .commands import CommandError
        raise CommandError('Must align equal numbers of atoms, got %d and %d'
                           % (atoms.count(), ref_atoms.count()))

    tf, rmsd = align_points(atoms.coordinates(), ref_atoms.coordinates())

    if report_matrix:
        write_matrix(tf, atoms, ref_atoms)

    msg = 'RMSD between %d atom pairs is %.3f Angstroms' % (ref_atoms.count(), rmsd)
    from .gui import show_status, log_message
    show_status(msg)
    log_message(msg + '\n')

    if move is None:
        move = 'molecules'

    move_atoms(atoms, ref_atoms, tf, move)

    return tf, rmsd

#
# Computes rotation and translation to align one set of positions with another.
# The sum of the squares of the distances between corresponding positions is
# minimized.  The xyz positions are specified as n by 3 numpy arrays.
# Returns 3 by 4 transform matrix and rms value.
#
def align_points(xyz, ref_xyz):

    # TODO: Testing if float64 has less roundoff error.
    from numpy import float64
    xyz = xyz.astype(float64)
    ref_xyz = ref_xyz.astype(float64)

    center = xyz.mean(axis = 0)
    ref_center = ref_xyz.mean(axis = 0)
    if len(xyz) == 1:
        # No rotation if aligning one point.
        from numpy import array, float64
        tf = array(((1,0,0,0),(0,1,0,0),(0,0,1,0)), float64)
        tf[:,3] = ref_center - center
        rms = 0
    else:
        Si = xyz - center
        Sj = ref_xyz - ref_center
        from numpy import dot, transpose, trace, zeros, empty, float64, identity
        Sij = dot(transpose(Si), Sj)
        M = zeros((4,4), float64)
        M[:3,:3] = Sij
        MT = transpose(M)
        trM = trace(M)*identity(4, float64)
        P = M + MT - 2 * trM
        P[3, 0] = P[0, 3] = M[1, 2] - M[2, 1]
        P[3, 1] = P[1, 3] = M[2, 0] - M[0, 2]
        P[3, 2] = P[2, 3] = M[0, 1] - M[1, 0]
        P[3, 3] = 0.0

        # Find the eigenvalues and eigenvectors
        from numpy import linalg
        evals, evecs = linalg.eig(P)    # eigenvectors are columns
        q = evecs[:,evals.argmax()]
        R = quaternion_rotation_matrix(q)
        tf = empty((3,4), float64)
        tf[:,:3] = R
        tf[:,3] = ref_center - dot(R,center)

        # Compute RMS
        # TODO: This RMS calculation has rather larger round-off errors
        #  probably from subtracting two large numbers.
        rms2 = (Si*Si).sum() + (Sj*Sj).sum() - 2 * (transpose(R)*Sij).sum()
        from math import sqrt
        rms = sqrt(rms2/len(Si)) if rms2 >= 0 else 0
#        df = dot(Sj,R) - Si
#        arms = sqrt((df*df).sum()/len(Si))
#        print (rms, arms)

    return tf, rms

def quaternion_rotation_matrix(q):
    l,m,n,s = q
    l2 = l*l
    m2 = m*m
    n2 = n*n
    s2 = s*s
    lm = l*m
    ln = l*n
    ls = l*s
    ns = n*s
    mn = m*n
    ms = m*s
    m = ((l2 - m2 - n2 + s2, 2 * (lm - ns), 2 * (ln + ms)),
         (2 * (lm + ns), - l2 + m2 - n2 + s2, 2 * (mn - ls)),
         (2 * (ln - ms), 2 * (mn + ls), - l2 - m2 + n2 + s2))
    return m

def paired_atoms(atoms, ref_atoms):
    cas = atoms.separate_chains()
    cras = ref_atoms.separate_chains()
    from .molecule import Atom_Set
    paset = Atom_Set()
    praset = Atom_Set()
    for i in range(min(len(cas), len(cras))):
        ca, cra = cas[i], cras[i]
        m, a = ca.molatoms[0]
        rm, ra = cra.molatoms[0]
        pa, pra = pairing(m.residue_nums[a], rm.residue_nums[ra])
        paset.add_atoms(m, a[pa])
        praset.add_atoms(rm, ra[pra])
    return paset, praset

def pairing(rnums1, rnums2):
    p1 = []
    p2 = []
    i1 = i2 = 0
    n1, n2 = len(rnums1), len(rnums2)
    while i1 < n1 and i2 < n2:
        r1, r2 = rnums1[i1], rnums2[i2]
        if r1 == r2:
            p1.append(i1)
            p2.append(i2)
            i1 += 1
            i2 += 1
        elif r1 < r2:
            i1 += 1
        else:
            i2 += 1
    return p1, p2
    
def write_matrix(tf, atoms, ref_atoms):

    import Matrix as M
    m = atoms.molecules()[0]
    mp = m.place
    mpinv = M.invert_matrix(mtf)
    mtf = M.multiply_matrices(mpinv, tf, mp)
    dtf = M.transformation_description(mtf)
    msg = ('Alignment matrix in molecule %s coordinates\n%s' % dtf)
    from .gui import log_message
    log_message(msg)

def move_atoms(atoms, ref_atoms, tf, move):

    if move == 'molecules' or move is True:
        from .matrix import multiply_matrices
        for m in atoms.molecules():
            m.place = multiply_matrices(tf, m.place)
            m.redraw_needed = True
    else:
        if move == 'atoms':
            matoms = atoms
        elif move == 'residues':
            matoms = atoms.extend_to_residues()
        elif move == 'chains':
            matoms = atoms.extend_to_chains()
        elif isinstance(move, (tuple, list, set)):
            matoms = move
        else:
            return	# Move nothing

        matoms.move_atoms(tf)

def test_align_points(n = 100):
    from numpy import random, float32
    p = random.random((n,3)).astype(float32)
    axis = (.5,-.3,1)
    angle = 128
    shift = (10,20,30)
    from . import matrix as M
    tf = M.multiply_matrices(M.translation_matrix(shift),
                             M.rotation_transform(axis, angle))
    rp = p.copy()
    M.transform_points(rp, tf)
    atf, rms = align_points(p, rp)
    M.transform_points(p, atf)
    dp = p - rp
    from math import sqrt
    arms = sqrt((dp*dp).sum())
    print ('align %d points' % n, atf - tf, rms, arms)

def align_command(cmdname, args):

    from .commands import atoms_arg, string_arg, bool_arg, parse_arguments
    req_args = (('atoms', atoms_arg),
                ('ref_atoms', atoms_arg))
    opt_args = ()
    kw_args = (('move', string_arg),
               ('each', string_arg),
               ('same', string_arg),
               ('show_matrix', bool_arg))

    kw = parse_arguments(cmdname, args, req_args, opt_args, kw_args)
    align(**kw)
