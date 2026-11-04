// Every downloaded library item is complete and the right size: its model and thumbnail exist, its
// id is unique (also against the items built in code), its category is one the sidebar knows, it
// faces a valid way, its credit is filled in, and the model's bounds times its scale match the
// dimensions the card shows. Run: node --test scripts/test-library.mjs  (no browser needed).
// For the Neptune twin's scripts/ folder; added with the Construction Site packs.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { getBounds } from '@gltf-transform/functions';
import { MeshoptDecoder } from 'meshoptimizer';

const ROOT = new URL('../', import.meta.url);
const LIB = new URL('public/library/', ROOT);
const catalog = JSON.parse(readFileSync(new URL('library.json', LIB), 'utf8'));
const librarySrc = readFileSync(new URL('src/library.js', ROOT), 'utf8');
const CATEGORIES = [...librarySrc.match(/CATEGORY_ORDER\s*=\s*\[([\s\S]*?)\]/)[1].matchAll(/'([^']+)'/g)].map(m => m[1]);
const builtIn = new Set(readdirSync(new URL('src/', ROOT)).filter(f => f.endsWith('.js'))
	.flatMap(f => [...readFileSync(new URL(`src/${f}`, ROOT), 'utf8').matchAll(/\bid:\s*'([a-z0-9-]+)'/g)].map(m => m[1])));

test('ids are well formed and unique', () => {
	const ids = catalog.map(i => i.id);
	for (const id of ids) assert.match(id, /^[a-z0-9-]+$/);
	assert.equal(new Set(ids).size, ids.length, 'a library.json id appears twice');
	const clash = ids.filter(id => builtIn.has(id));
	assert.deepEqual(clash, [], 'library.json ids that are also ids of items built in code');
});

for (const item of catalog) {
	test(`${item.id}: complete`, () => {
		assert.ok(item.name && item.category, 'name and category');
		assert.ok(CATEGORIES.includes(item.category), `category ${item.category} is not in CATEGORY_ORDER`);
		assert.ok(['+z', '-z', '+x', '-x'].includes(item.front), `front ${item.front}`);
		assert.ok(item.scale > 0, 'scale');
		const file = new URL(item.file, LIB);
		assert.ok(existsSync(file), `${item.file} is missing`);
		assert.ok(Math.abs(statSync(file).size / 1024 - item.sizeKB) <= Math.max(2, item.sizeKB * 0.02), 'sizeKB is out of date');
		assert.ok(item.thumb?.endsWith('.webp') && existsSync(new URL(item.thumb, LIB)), 'a .webp thumbnail');
		assert.ok(statSync(new URL(item.thumb, LIB)).size > 1000, 'thumbnail is not blank');
		for (const key of ['title', 'url', 'author', 'license', 'site']) assert.ok(item.source?.[key], `source.${key}`);
		for (const key of ['length', 'width', 'height']) assert.ok(item.dimensions?.[key] > 0, `dimensions.${key}`);
	});
}

test('model bounds match the dimensions on the card', async () => {
	await MeshoptDecoder.ready;
	const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
	const wrong = [];
	for (const item of catalog) {
		if (item.recenter === false) continue;
		const doc = await io.read(new URL(item.file, LIB).pathname);
		// a rigged model's static bounds are its unposed skeleton's, not the machine: the importer
		// measures those in their bind pose instead, so they are left to it
		if (doc.getRoot().listSkins().length) continue;
		const { min, max } = getBounds(doc.getRoot().listScenes()[0]);
		const size = [0, 1, 2].map(k => (max[k] - min[k]) * item.scale);
		const alongX = item.front.endsWith('x');
		const [length, width] = alongX ? [size[0], size[2]] : [size[2], size[0]];
		const off = (a, b) => Math.abs(a - b) > Math.max(0.05, 0.05 * b);
		const d = item.dimensions;
		if (off(length, d.length) || off(width, d.width) || off(size[1], d.height))
			wrong.push(`${item.id}: model ${length.toFixed(2)} x ${width.toFixed(2)} x ${size[1].toFixed(2)} m, card ${d.length} x ${d.width} x ${d.height}`);
	}
	assert.deepEqual(wrong, [], 'items whose card size does not match the model');
});
