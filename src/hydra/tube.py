# -----------------------------------------------------------------------------
# Create tube surface geometry passing through specified points.
#
def tube_through_points(path, radius = 1.0, band_length = 0,
                        segment_subdivisions = 10, circle_subdivisions = 15,
                        color = (.745,.745,.745,1)):
#    from time import process_time
#    t0 = process_time()

    from ._image3d import natural_cubic_spline, tube_geometry
    spath, stan = natural_cubic_spline(path, segment_subdivisions)

    circle = circle_points(circle_subdivisions, radius)
    circle_normals = circle_points(circle_subdivisions, 1.0)
    va,na,ta = tube_geometry(spath, stan, circle, circle_normals)

    from numpy import empty, float32
    ca = empty((len(va),4), float32)
    ca[:,:] = color

#    t1 = process_time()
#    print ('tube', len(path), t1-t0)

    return va,na,ta,ca

# -----------------------------------------------------------------------------
#
def circle_points(n, radius):

    from numpy import arange, float32, empty, sin, cos
    from math import pi
    a = arange(n) * (2*pi/n)
    c = empty((n,3), float32)
    c[:,0] = radius*cos(a)
    c[:,1] = radius*sin(a)
    c[:,2] = 0
    return c

# -----------------------------------------------------------------------------
# Create tube surface geometry passing through specified points.
#
def tube_through_points_old(path, radius = 1.0, band_length = 0,
                        segment_subdivisions = 10, circle_subdivisions = 15,
                        color = (.745,.745,.745,1)):

    def shape(path, tangents, pcolors, r=radius, nc=circle_subdivisions):
        return Tube(path, tangents, pcolors, r, nc)

    from time import process_time
    t0 = process_time()
    va,na,ta,ca = extrusion(path, shape, band_length, segment_subdivisions, color)
    t1 = process_time()
    print ('tube', len(path), t1-t0)

    return va,na,ta,ca

# -----------------------------------------------------------------------------
#
class Tube:

    def __init__(self, path, tangents, pcolors, radius, circle_subdivisions,
                 end_caps = True):

        self.path = path                # Center line points
        self.tangents = tangents        # Tangents for each point
        self.pcolors = pcolors  # Point colors.
        self.radius = radius
        self.circle_subdivisions = circle_subdivisions
        self.end_caps = end_caps

    def geometry(self):

        nz = len(self.path)
        nc = self.circle_subdivisions
        height = 0
        from time import process_time
        t0 = process_time()
        tflist = extrusion_transforms(self.path, self.tangents)
        t1 = process_time()
        print ('ext trans', t1-t0)
        from .matrix import zero_translation
        tfnlist = [zero_translation(tf) for tf in tflist]
        t2 = process_time()
        print ('n trans', t2-t1)
        varray, narray, tarray = cylinder_geometry(self.radius, height, nz, nc,
                                                   caps = self.end_caps)
        t3 = process_time()
        print ('cyl geom', t3-t2)
        # Transform circles.
        from ._image3d import affine_transform_vertices
        for i in range(nz):
            affine_transform_vertices(varray[nc*i:nc*(i+1),:], tflist[i])
            affine_transform_vertices(narray[nc*i:nc*(i+1),:], tfnlist[i])
        t4 = process_time()
        print ('trans circ', t4-t3)

        if self.end_caps:
            # Transform cap center points
            affine_transform_vertices(varray[-2:-1,:], tflist[0])
            affine_transform_vertices(narray[-2:-1,:], tfnlist[0])
            affine_transform_vertices(varray[-1:,:], tflist[-1])
            affine_transform_vertices(narray[-1:,:], tfnlist[-1])

        t5 = process_time()
        print ('trans cap', t5-t4)

        return varray, narray, tarray

    def colors(self):

        nc = self.circle_subdivisions
        nz = len(self.pcolors)
        from numpy import empty, float32
        vcount = nz*nc+2 if self.end_caps else nc*nc
        carray = empty((vcount,4), float32)
        for i in range(nz):
            carray[nc*i:nc*(i+1),:] = self.pcolors[i]
        if self.end_caps:
            carray[-2,:] = self.pcolors[0]
            carray[-1,:] = self.pcolors[-1]
        return carray

# -----------------------------------------------------------------------------
#
def cylinder_geometry(radius, height, nz, nc, caps):

    varray, narray, tarray = tube_geometry(nz, nc)
    varray[:,0] *= radius
    varray[:,1] *= radius
    varray[:,2] *= height
   
    if not caps:
        return varray, narray, tarray

    vc = varray.shape[0]
    varray.resize((vc+2,3))
    narray.resize((vc+2,3))
    varray[vc,:] = (0,0,-0.5*height)
    varray[vc+1,:] = (0,0,0.5*height)
    narray[vc,:] = (0,0,-1)
    narray[vc+1,:] = (0,0,1)

    tc = tarray.shape[0]
    tarray.resize((tc+2*nc,3))
    for i in range(nc):
        tarray[tc+i,:] = (vc,(i+1)%nc,i)
        tarray[tc+nc+i,:] = (vc+1,vc-nc+i,vc-nc+(i+1)%nc)

    return varray, narray, tarray

# -----------------------------------------------------------------------------
# Build a hexagonal lattice tube
#
def tube_geometry(nz, nc):

    from numpy import empty, float32, arange, cos, sin, int32, pi
    vc = nz*nc
    tc = (nz-1)*nc*2
    varray = empty((vc,3), float32)
    narray = empty((vc,3), float32)
    tarray = empty((tc,3), int32)

    # Calculate vertices
    v = varray.reshape((nz,nc,3))
    angles = (2*pi/nc)*arange(nc)
    v[::2,:,0] = cos(angles)
    v[::2,:,1] = sin(angles)
    angles += pi/nc
    v[1::2,:,0] = cos(angles)
    v[1::2,:,1] = sin(angles)
    for z in range(nz):
        v[z,:,2] = float(z)/(nz-1) - 0.5

    # Set normals
    narray[:,:] = varray
    narray[:,2] = 0

    # Create triangles
    t = tarray.reshape((nz-1,nc,6))
    c = arange(nc)
    c1 = (c+1)%nc
    t[:,:,0] = t[1::2,:,3] = c
    t[::2,:,1] = t[::2,:,3] = t[1::2,:,1] = c1
    t[::2,:,4] = t[1::2,:,2] = t[1::2,:,4] = c1+nc
    t[::2,:,2] = t[:,:,5] = c+nc
    for z in range(1,nz-1):
        t[z,:,:] += z*nc

    return varray, narray, tarray

# -----------------------------------------------------------------------------
#
def extrusion(path, shape, band_length = 0, segment_subdivisions = 10,
              color = (.745,.745,.745,1)):

    point_colors = [color]*len(path)
    segment_colors = [color] * (len(path) - 1)
    va,na,ta,ca = banded_extrusion(path, point_colors, segment_colors,
                                   segment_subdivisions, band_length, shape)
    return va,na,ta,ca

# -----------------------------------------------------------------------------
# Create an extruded surface along a path with banded coloring.
#
def banded_extrusion(xyz_path, point_colors, segment_colors,
                     segment_subdivisions, band_length, shape):

    if len(xyz_path) <= 1:
        return None             # No path

    from .spline import natural_cubic_spline
#    from ._image3d import natural_cubic_spline
    from time import process_time
    t0 = process_time()
    spath, stan = natural_cubic_spline(xyz_path, segment_subdivisions)

    t1 = process_time()
    print ('spline', t1-t0)

    pcolors = band_colors(spath, point_colors, segment_colors,
                          segment_subdivisions, band_length)

    s = shape(spath, stan, pcolors)
    t0 = process_time()
    va, na, ta = s.geometry()
    t1 = process_time()
    print ('geom', t1-t0)
    ca = s.colors()

    return va,na,ta,ca

# -----------------------------------------------------------------------------
# Compute transforms mapping (0,0,0) origin to points along path with z axis
# along path tangent.
#
def extrusion_transforms(path, tangents, yaxis = None):

    from . import matrix as M
    tflist = []
    if yaxis is None:
        # Make xy planes for coordinate frames at each path point not rotate
        # from one point to next.
        tf = M.identity_matrix()
        n0 = (0,0,1)
        for p1,n1 in zip(path, tangents):
            tf = M.multiply_matrices(M.vector_rotation_transform(n0,n1), tf)
            tflist.append(M.multiply_matrices(M.translation_matrix(p1),tf))
            n0 = n1
    else:
        # Make y-axis of coordinate frames at each point align with yaxis.
        for p,t in zip(path, tangents):
            za = t
            xa = M.normalize_vector(M.cross_product(yaxis, za))
            ya = M.cross_product(za, xa)
            tf = ((xa[0], ya[0], za[0], p[0]),
                  (xa[1], ya[1], za[1], p[1]),
                  (xa[2], ya[2], za[2], p[2]))
            tflist.append(tf)
    return tflist

# -----------------------------------------------------------------------------
# Calculate point colors for an interpolated set of points.
# Point colors are extended to interpolated points and segments within
# band_length/2 arc distance.
#
def band_colors(plist, point_colors, segment_colors,
                segment_subdivisions, band_length):

  n = len(point_colors)
  pcolors = []
  for k in range(n-1):
    j = k * (segment_subdivisions + 1)
    from . import spline
    arcs = spline.arc_lengths(plist[j:j+segment_subdivisions+2])
    bp0, mp, bp1 = band_points(arcs, band_length)
    scolors = ([point_colors[k]]*bp0 +
               [segment_colors[k]]*mp +
               [point_colors[k+1]]*bp1)
    pcolors.extend(scolors[:-1])
  if band_length > 0:
      last = point_colors[-1]
  else:
      last = segment_colors[-1]
  pcolors.append(last)
  return pcolors
  
# -----------------------------------------------------------------------------
# Count points within band_length/2 of each end of an arc.
#
def band_points(arcs, band_length):
      
  arc = arcs[-1]
  half_length = min(.5 * band_length, .5 * arc)
  bp0 = mp = bp1 = 0
  for p in range(len(arcs)):
    l0 = arcs[p]
    l1 = arc - arcs[p]
    if l0 < half_length:
      if l1 < half_length:
        if l0 <= l1:
          bp0 += 1
        else:
          bp1 += 1
      else:
        bp0 += 1
    elif l1 < half_length:
      bp1 += 1
    else:
      mp += 1

  return bp0, mp, bp1
