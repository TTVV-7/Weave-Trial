#!/usr/bin/env node
// Studio preview renders for .glb and .stl models, in headless Chromium + three.js.
//
//   node construction_site/render_previews.mjs [--az 35] [--el 22] [--size 1200x900] model.glb ...
//   node construction_site/render_previews.mjs --scene layout.json --out hero.png
//
// Each model gets <stem>_preview.png beside it. --az is the camera's bearing from
// the model's front (+X) towards its left (+Y), --el its height, both in degrees.
// A scene file is a list of {"file", "x", "y", "rot"} in metres and degrees.
//
// Needs Playwright (with its Chromium) and three.js: run  npm install  in construction_site/
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import path from 'node:path';

const require = createRequire(import.meta.url);

function load(name) {
  try { return require(name); } catch {}
  return require(path.join(execSync('npm root -g').toString().trim(), name));
}

function threeDir() {
  if (process.env.THREE_DIR) return process.env.THREE_DIR;
  for (const base of [process.cwd(), path.dirname(new URL(import.meta.url).pathname)]) {
    try { return path.resolve(path.dirname(createRequire(path.join(base, 'x.js')).resolve('three')), '..'); } catch {}
  }
  console.error('three.js not found: run  npm install  in construction_site/  (or set THREE_DIR)');
  process.exit(1);
}

const args = process.argv.slice(2);
const opt = { az: 35, el: 22, size: '1200x900', scene: null, out: null, color: '#9aa0a6' };
const files = [];
for (let i = 0; i < args.length; i++) {
  const a = args[i];
  if (a.startsWith('--')) opt[a.slice(2)] = args[++i];
  else files.push(a);
}
const [W, H] = opt.size.split('x').map(Number);
const THREE_DIR = threeDir();
const { chromium } = load('playwright');

const PAGE = `<!doctype html><html><head><style>html,body{margin:0;background:#fff}</style>
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
</head><body><script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { STLLoader } from 'three/addons/loaders/STLLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';

function backdrop() {
  const c = document.createElement('canvas'); c.width = 4; c.height = 256;
  const g = c.getContext('2d'), grad = g.createLinearGradient(0, 0, 0, 256);
  grad.addColorStop(0, '#f6f7f9'); grad.addColorStop(1, '#d9dde3');
  g.fillStyle = grad; g.fillRect(0, 0, 4, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}

async function loadModel(url, color) {
  if (url.endsWith('.stl')) {
    const geo = await new STLLoader().loadAsync(url);
    geo.computeVertexNormals();
    const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0.0 }));
    mesh.rotation.x = -Math.PI / 2;             // STL is Z up, in mm
    const g = new THREE.Group(); g.add(mesh); g.scale.setScalar(0.001); return g;
  }
  return (await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(url)).scene;   // meshopt: Neptune's format
}

window.render = async ({ items, W, H, az, el, color }) => {
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1); renderer.setSize(W, H);
  renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.NeutralToneMapping; renderer.toneMappingExposure = 0.9;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  document.body.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = backdrop();
  const pmrem = new THREE.PMREMGenerator(renderer);
  scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  scene.environmentIntensity = 0.55;

  const root = new THREE.Group();
  for (const it of items) {
    const m = await loadModel(it.url, color);
    const holder = new THREE.Group();
    holder.add(m);
    holder.rotation.y = (it.rot || 0) * Math.PI / 180;
    holder.position.set(it.x || 0, 0, -(it.y || 0));   // CAD (x, y) -> three (x, -z)
    root.add(holder);
  }
  root.traverse(o => { if (o.isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  scene.add(root);

  const box = new THREE.Box3().setFromObject(root);
  const sphere = box.getBoundingSphere(new THREE.Sphere());
  const r = sphere.radius, c = sphere.center;

  const ground = new THREE.Mesh(new THREE.PlaneGeometry(r * 40, r * 40), new THREE.ShadowMaterial({ opacity: 0.22 }));
  ground.rotation.x = -Math.PI / 2; ground.position.y = box.min.y; ground.receiveShadow = true;
  scene.add(ground);

  scene.add(new THREE.HemisphereLight(0xffffff, 0xa4abb5, 0.6));
  const key = new THREE.DirectionalLight(0xffffff, 2.2);
  const toRad = Math.PI / 180;
  const keyDir = new THREE.Vector3(Math.cos((az + 40) * toRad), 1.6, -Math.sin((az + 40) * toRad)).normalize();
  key.position.copy(c).addScaledVector(keyDir, r * 3); key.target.position.copy(c);
  key.castShadow = true; key.shadow.mapSize.set(4096, 4096);
  Object.assign(key.shadow.camera, { left: -r * 1.3, right: r * 1.3, top: r * 1.3, bottom: -r * 1.3, near: r * 0.5, far: r * 6 });
  key.shadow.bias = -0.0004; key.shadow.normalBias = r * 0.002; key.shadow.radius = 3;
  scene.add(key, key.target);
  const fill = new THREE.DirectionalLight(0xdfe8ff, 0.6);
  fill.position.copy(c).add(new THREE.Vector3(Math.cos((az - 50) * toRad), 0.5, -Math.sin((az - 50) * toRad)).multiplyScalar(r * 3));
  scene.add(fill);

  // camera: bearing az from +X towards +Y (CAD), i.e. towards -Z in three
  const cam = new THREE.PerspectiveCamera(26, W / H, r / 200, r * 100);
  const dir = new THREE.Vector3(Math.cos(el * toRad) * Math.cos(az * toRad), Math.sin(el * toRad),
                                -Math.cos(el * toRad) * Math.sin(az * toRad));
  // fit to the geometry itself, not its bounding box: a tall mast would leave the frame mostly empty
  const corners = [];
  root.updateMatrixWorld(true);
  root.traverse(o => {
    if (!o.isMesh) return;
    const pos = o.geometry.attributes.position, step = Math.max(1, Math.floor(pos.count / 4000));
    for (let i = 0; i < pos.count; i += step)
      corners.push(new THREE.Vector3().fromBufferAttribute(pos, i).applyMatrix4(o.matrixWorld));
  });
  let target = c.clone(), dist = r * 3;
  for (let it = 0; it < 6; it++) {          // fit the box to 86% of the frame, centred
    cam.position.copy(target).addScaledVector(dir, dist); cam.lookAt(target); cam.updateMatrixWorld();
    let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
    for (const p of corners) { const q = p.clone().project(cam); x0 = Math.min(x0, q.x); x1 = Math.max(x1, q.x); y0 = Math.min(y0, q.y); y1 = Math.max(y1, q.y); }
    const span = Math.max((x1 - x0) / 2, (y1 - y0) / 2);
    const right = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 1);
    const half = Math.tan(cam.fov * toRad / 2) * dist;
    target.addScaledVector(right, (x0 + x1) / 2 * half * cam.aspect).addScaledVector(up, (y0 + y1) / 2 * half);
    dist *= span / 0.86;
  }
  cam.position.copy(target).addScaledVector(dir, dist); cam.lookAt(target);
  renderer.render(scene, cam);
  return renderer.domElement.toDataURL('image/png');
};
window.ready = true;
</script></body></html>`;

const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });

async function renderItems(items, out) {
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  const served = new Map(items.map((it, i) => [`/model/${i}${path.extname(it.file)}`, it.file]));
  await page.route('http://render.local/**', route => {
    const p = new URL(route.request().url()).pathname;
    if (p === '/') return route.fulfill({ contentType: 'text/html', body: PAGE });
    let file = served.get(p);
    if (!file && p.startsWith('/three/')) file = path.join(THREE_DIR, p.slice(7));
    if (!file || !existsSync(file)) return route.fulfill({ status: 404, body: 'not found' });
    const type = file.endsWith('.js') ? 'text/javascript' : 'application/octet-stream';
    return route.fulfill({ contentType: type, body: readFileSync(file) });
  });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.goto('http://render.local/');
  await page.waitForFunction(() => window.ready === true);
  const urls = items.map((it, i) => ({ ...it, url: `/model/${i}${path.extname(it.file)}` }));
  const data = await page.evaluate(o => window.render(o),
    { items: urls, W, H, az: Number(opt.az), el: Number(opt.el), color: opt.color });
  writeFileSync(out, Buffer.from(data.split(',')[1], 'base64'));
  await page.close();
  console.log('wrote', out);
}

if (opt.scene) {
  const items = JSON.parse(readFileSync(opt.scene, 'utf8'))
    .map(it => ({ ...it, file: path.resolve(path.dirname(opt.scene), it.file) }));
  await renderItems(items, opt.out || opt.scene.replace(/\.json$/, '.png'));
} else {
  for (const f of files) {
    const out = opt.out && files.length === 1 ? opt.out : f.replace(/\.(glb|stl)$/i, '_preview.png');
    await renderItems([{ file: path.resolve(f) }], out);
  }
}
await browser.close();
