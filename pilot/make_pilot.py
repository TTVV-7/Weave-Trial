import numpy as np, trimesh
from trimesh.creation import cylinder, box

# Real-world dimensions (mm), 2006 Honda Pilot (1st gen)
WB, FX = 2700, 960            # wheelbase, front axle x from front bumper
R_T, TW = 367, 230            # tire radius, tire width
HALF_W = 980

def hull(profile, width_fn):
    pts = [(x, s*width_fn(z), z) for x, z in profile for s in (-1, 1)]
    return trimesh.convex.convex_hull(np.array(pts, float))

# Lower body (side profile, x forward->back, z up)
lower = [(0,330),(0,700),(70,880),(330,1000),(1350,1080),(4720,1110),(4775,1040),(4775,330),(4600,300),(150,300)]
body = hull(lower, lambda z: 940 if z < 450 else HALF_W)

# Greenhouse: windshield, roof, rear hatch glass
gh = [(1360,1070),(2080,1760),(4520,1790),(4730,1110)]
green = hull(gh, lambda z: 975 if z < 1200 else 860)

# Roof rails
rails = [box(extents=(2000, 50, 50), transform=trimesh.transformations.translation_matrix((3350, s*720, 1805))) for s in (-1,1)]
# Side mirrors
mirrors = [box(extents=(120, 150, 110), transform=trimesh.transformations.translation_matrix((1500, s*1030, 1130))) for s in (-1,1)]

def ycyl(r, length, x, y, z):
    c = cylinder(radius=r, height=length, sections=64)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (1,0,0)))
    c.apply_translation((x, y, z))
    return c

axles_x = (FX, FX + WB)
# Wheel arch cutouts (only outer part of body)
arches = [ycyl(430, 400, x, s*(HALF_W - 150), R_T) for x in axles_x for s in (-1,1)]
wheels = [ycyl(R_T, TW, x, s*(HALF_W - 10 - TW/2), R_T) for x in axles_x for s in (-1,1)]
hubs   = [ycyl(200, 30, x, s*(HALF_W - 10), R_T) for x in axles_x for s in (-1,1)]
axles  = [ycyl(120, 2*HALF_W - 100, x, 0, R_T) for x in axles_x]

shell = trimesh.boolean.union([body, green] + rails + mirrors, engine="manifold")
shell = trimesh.boolean.difference([shell] + arches, engine="manifold")
car = trimesh.boolean.union([shell] + wheels + hubs + axles, engine="manifold")
# Flatten tire bottoms slightly so it sits flat on the bed
car = trimesh.boolean.intersection([car, box(bounds=((-100,-1200,25),(5000,1200,3000)))], engine="manifold")

car.apply_scale(1/43)                 # 1:43 scale
car.apply_translation(-car.bounds[0]) # sit on z=0 at origin
print("watertight:", car.is_watertight, "size mm:", np.round(car.extents, 1), "faces:", len(car.faces))
car.export("pilot/honda_pilot_2006_1-43.3mf")

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig = plt.figure(figsize=(10,6)); ax = fig.add_subplot(projection="3d")
n = car.face_normals; light = np.clip(n @ np.array([0.4,-0.6,0.7])/np.linalg.norm([0.4,-0.6,0.7]),0.15,1)
ax.add_collection3d(Poly3DCollection(car.triangles, facecolors=plt.cm.Blues(0.35+0.6*light), edgecolor="none"))
e = car.extents; ax.set_xlim(0,e[0]); ax.set_ylim(-(e[0]-e[1])/2, e[1]+(e[0]-e[1])/2); ax.set_zlim(0,e[0]*0.6)
ax.view_init(elev=18, azim=-55); ax.set_axis_off()
plt.savefig("pilot/preview.png", dpi=110, bbox_inches="tight")
