"""Do the exported STL / 3MF hold the same bodies that make_capybara() returns?"""
import sys, zipfile, re, importlib.util
import numpy as np, trimesh, manifold3d as mf
J = '/home/user/Weave-Trial/fidgets/attempts/joints/'
spec = importlib.util.spec_from_file_location('joints_capybara', J + 'make_capybara.py')
mc = importlib.util.module_from_spec(spec); spec.loader.exec_module(mc)
for name, maker in (("pocket-capybara", mc.make_capybara), ("pocket-capybara-test", mc.make_test)):
    parts, _, _ = maker()
    m = trimesh.load(J + name + '.stl', process=True)
    comps = m.split(only_watertight=False)
    print(name, 'STL tris', len(m.faces), 'bounds', np.round(m.bounds, 3).tolist(), 'components', len(comps),
          'watertight each', [bool(c.is_watertight) for c in comps])
    vs = sorted(round(float(c.volume), 2) for c in comps)
    vp = sorted(round(float(p.volume()), 2) for p in parts.values())
    print('  STL volumes ', vs); print('  part volumes', vp)
    print('  STL zmin per component', sorted(round(float(c.bounds[0][2]), 5) for c in comps))
    z = zipfile.ZipFile(J + name + '.3mf')
    print('  3mf entries', [(i.filename, i.file_size) for i in z.infolist()])
    for i in z.infolist():
        if i.filename.endswith('.model'):
            t = z.read(i).decode()
            print('  model head:', t[:400].replace('\n', ' '))
            print('  vertices', t.count('<vertex '), 'triangles', t.count('<triangle '), 'objects', t.count('<object '),
                  'items', re.findall(r'<item [^>]*>', t)[:3], 'paint attrs', len(re.findall(r'paint_color="', t)))
            zs = np.array([float(v) for v in re.findall(r'<vertex [^>]*z="([-0-9.e]+)"', t)])
            print('  3mf z range', zs.min(), zs.max())
