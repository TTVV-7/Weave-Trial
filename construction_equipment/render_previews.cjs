#!/usr/bin/env node
// Render <name>_preview.png for each GLB in this folder, the thumbnail the
// model library shows.
//
//     node construction_equipment/render_previews.cjs                 # every .glb here
//     node construction_equipment/render_previews.cjs Wheel_Loader_18t
//
// Needs Playwright's Chromium and internet access: it draws with the same
// three.js the dashboard loads from jsDelivr, lit with three's RoomEnvironment
// so the PBR metal parts read as metal rather than black. The camera looks from
// the front-left and above, the direction the dashboard's own thumbnails use.

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const HERE = __dirname;
const W = 800, H = 600;

const PAGE = `<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;background:#fff}canvas{display:block}</style>
<script type="importmap">{"imports":{
  "three":"https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
  "three/addons/":"https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
</head><body><script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setSize(${W}, ${H});
renderer.setClearColor(0xffffff, 1);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

window.render = async (url) => {
  const scene = new THREE.Scene();
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  const model = (await new GLTFLoader().loadAsync(url)).scene;
  model.traverse(o => { if (o.isMesh) o.castShadow = true; });
  scene.add(model);

  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3()), centre = box.getCenter(new THREE.Vector3());
  const radius = size.length() / 2;

  // a soft shadow under the machine, so it sits on the ground
  const sun = new THREE.DirectionalLight(0xffffff, 1.2);
  sun.position.set(centre.x + radius * 0.6, radius * 3, centre.z + radius * 0.9);
  sun.target.position.copy(centre);
  sun.castShadow = true;
  sun.shadow.mapSize.set(2048, 2048);
  Object.assign(sun.shadow.camera, { left: -radius, right: radius, top: radius, bottom: -radius,
                                     near: 0.1, far: radius * 8 });
  sun.shadow.radius = 6;
  scene.add(sun, sun.target);
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(radius * 8, radius * 8),
                                new THREE.ShadowMaterial({ opacity: 0.18 }));
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(centre.x, box.min.y, centre.z);
  ground.receiveShadow = true;
  scene.add(ground);

  // frame the box, not its bounding sphere: aim at the middle of the box's
  // projected outline and move in until that outline fills most of the frame
  const camera = new THREE.PerspectiveCamera(30, ${W} / ${H}, radius / 100, radius * 100);
  const dir = new THREE.Vector3(1, 0.75, 1.25).normalize();
  const corners = [];
  for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y])
    for (const z of [box.min.z, box.max.z]) corners.push(new THREE.Vector3(x, y, z));
  let target = centre.clone(), dist = radius / Math.sin(THREE.MathUtils.degToRad(camera.fov / 2));
  for (let i = 0; i < 8; i++) {
    camera.position.copy(target).addScaledVector(dir, dist);
    camera.lookAt(target); camera.updateMatrixWorld();
    const p = corners.map(c => c.clone().project(camera));
    const xs = p.map(v => v.x), ys = p.map(v => v.y);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    // shift the aim toward the outline's middle, in the camera's own right/up axes
    const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
    const halfW = dist * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * camera.aspect;
    const halfH = dist * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
    target.addScaledVector(right, (x0 + x1) / 2 * halfW).addScaledVector(up, (y0 + y1) / 2 * halfH);
    dist *= Math.max((x1 - x0) / 2, (y1 - y0) / 2) / 0.98;
  }
  camera.position.copy(target).addScaledVector(dir, dist);
  camera.lookAt(target);
  renderer.render(scene, camera);
  return [size.x, size.y, size.z];
};
window.ready = true;
</script></body></html>`;

(async () => {
  const wanted = process.argv.slice(2);
  const files = fs.readdirSync(HERE).filter(f => f.endsWith('.glb'))
    .filter(f => !wanted.length || wanted.includes(path.basename(f, '.glb')));
  const browser = await chromium.launch({ args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on('pageerror', e => console.error('page error:', e.message));
  await page.route('http://models.local/**', route => {
    const name = decodeURIComponent(new URL(route.request().url()).pathname.slice(1));
    route.fulfill({ body: fs.readFileSync(path.join(HERE, name)), contentType: 'model/gltf-binary' });
  });
  await page.route('http://page.local/', route => route.fulfill({ body: PAGE, contentType: 'text/html' }));
  await page.goto('http://page.local/');
  await page.waitForFunction(() => window.ready, null, { timeout: 60000 });
  for (const f of files) {
    const size = await page.evaluate(u => window.render(u), `http://models.local/${encodeURIComponent(f)}`);
    const out = path.join(HERE, path.basename(f, '.glb') + '_preview.png');
    await page.locator('canvas').screenshot({ path: out });
    console.log(`${path.basename(out)}  (model ${size.map(v => v.toFixed(2)).join(' x ')} m)`);
  }
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
