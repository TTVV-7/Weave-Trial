#!/usr/bin/env node
// Slim one GLB for the Neptune twin and print what its library entry needs, as JSON.
//
//   node construction_site/neptune/optimize.mjs in.glb out.glb
//
// The same steps as the twin's own scripts/add-asset.mjs (dedup, prune, weld, meshopt), plus
// palette + flatten + join: a model's flat colours go into one small palette texture so its parts
// merge into one mesh. The twin draws a Row as one InstancedMesh per mesh, so a 150-part machine
// would otherwise cost 150 draw calls per row; joined it costs one or two (glass stays apart).
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup, flatten, getBounds, join, meshopt, palette, prune, weld } from '@gltf-transform/functions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';

const [input, output] = process.argv.slice(2);
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS)
	.registerDependencies({ 'meshopt.decoder': MeshoptDecoder, 'meshopt.encoder': MeshoptEncoder });
await MeshoptEncoder.ready;
const quiet = { warn() {}, info() {}, debug() {}, error: console.error };
const doc = await io.read(input);
doc.setLogger(quiet);
await doc.transform(dedup(), palette({ min: 2 }), flatten(), join(), prune(), weld(),
	meshopt({ encoder: MeshoptEncoder, level: 'medium' }));
const scene = doc.getRoot().getDefaultScene() ?? doc.getRoot().listScenes()[0];
const { min, max } = getBounds(scene);
let triangles = 0, draws = 0;
for (const mesh of doc.getRoot().listMeshes()) for (const prim of mesh.listPrimitives()) {
	draws += 1;
	const idx = prim.getIndices();
	triangles += (idx ? idx.getCount() : prim.getAttribute('POSITION').getCount()) / 3;
}
const bytes = await io.writeBinary(doc);
const { writeFile } = await import('node:fs/promises');
await writeFile(output, bytes);
console.log(JSON.stringify({ min, max, triangles, draws, bytes: bytes.byteLength }));
