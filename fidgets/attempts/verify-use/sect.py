from common import *
def poly_props(cs):
    """area, centroid (cx, cy), Ixx about centroid (int y^2 dA), Iyy about centroid (int x^2 dA) of a CrossSection"""
    A = Sx = Sy = Ixx = Iyy = 0.0
    for p in cs.to_polygons():
        p = np.asarray(p, float); q = np.roll(p, -1, 0)
        c = p[:,0]*q[:,1] - q[:,0]*p[:,1]
        A += c.sum()/2
        Sx += ((p[:,0]+q[:,0])*c).sum()/6
        Sy += ((p[:,1]+q[:,1])*c).sum()/6
        Ixx += ((p[:,1]**2 + p[:,1]*q[:,1] + q[:,1]**2)*c).sum()/12
        Iyy += ((p[:,0]**2 + p[:,0]*q[:,0] + q[:,0]**2)*c).sum()/12
    if A < 1e-9: return 0, (0,0), 0, 0, (0,0,0,0)
    cx, cy = Sx/A, Sy/A
    pts = np.concatenate([np.asarray(p, float) for p in cs.to_polygons()])
    return A, (cx, cy), Ixx - A*cy*cy, Iyy - A*cx*cx, (pts[:,0].min(), pts[:,0].max(), pts[:,1].min(), pts[:,1].max())
def zslice(m, z):
    return m.slice(float(z))
def xslice(m, x):
    """section by the plane x = const; returned in (y, z) coordinates"""
    # rotate so +x becomes +z: rotate about y by -90: (x,y,z)->( -z?, ...). use explicit transform
    T = np.array([[0,1,0,0],[0,0,1,0],[1,0,0,0]], float)   # new = (y, z, x)
    return m.transform(T).slice(float(x))
def yslice(m, y):
    """section by the plane y = const; returned in (z, x) coordinates"""
    T = np.array([[0,0,1,0],[1,0,0,0],[0,1,0,0]], float)   # new = (z, x, y)
    return m.transform(T).slice(float(y))
