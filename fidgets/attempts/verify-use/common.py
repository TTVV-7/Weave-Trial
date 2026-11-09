import sys, pathlib
sys.dont_write_bytecode = True
sys.path.insert(0, '/home/user/Weave-Trial/fidgets')
sys.path.insert(0, '/home/user/Weave-Trial/fidgets/attempts/joints')
import numpy as np, trimesh, manifold3d as mf
import make_fidgets as mk
import make_capybara as cb
import preview as pv
J = pathlib.Path('/home/user/Weave-Trial/fidgets/attempts/joints')
