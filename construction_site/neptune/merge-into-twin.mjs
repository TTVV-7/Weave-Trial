#!/usr/bin/env node
// Copy staged construction models into a checkout of the Neptune twin and record them in its library.
//
//   python construction_site/export_neptune.py --neptune <twin>      # stage first
//   node construction_site/neptune/merge-into-twin.mjs <twin> [construction_site/neptune/out]
//
// Mirrors the twin's own scripts/add-asset.mjs exactly when it records a model: the GLB goes to
// public/library/<id>.glb, its thumbnail to public/library/thumbs/<id>.webp, and its entry into
// public/library/library.json as { ...earlier entry, ...new entry }, so a replaced item keeps the
// fields added to it by hand (a machine's drive tuning, the Pro flag). The catalog is sorted and
// CREDITS.md rewritten the same way. Run it on a branch of the twin, never on its deploy branch.
import { copyFile, mkdir, readFile, writeFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';

const [twinArg, stageArg] = process.argv.slice(2);
if (!twinArg) { console.error('usage: merge-into-twin.mjs <twin checkout> [staging dir]'); process.exit(1); }
const twin = resolve(twinArg);
const stage = resolve(stageArg ?? new URL('./out', import.meta.url).pathname);
const LIB = join(twin, 'public', 'library');
const CATALOG = join(LIB, 'library.json');

const catalog = JSON.parse(await readFile(CATALOG, 'utf8'));
const staged = JSON.parse(await readFile(join(stage, 'library-entries.json'), 'utf8'));
await mkdir(join(LIB, 'thumbs'), { recursive: true });

let updated = catalog;
for (const { _merge, ...entry } of staged) {
	await copyFile(join(stage, 'public', 'library', entry.file), join(LIB, entry.file));
	await copyFile(join(stage, 'public', 'library', entry.thumb), join(LIB, entry.thumb));
	const previous = updated.find(item => item.id === entry.id);
	const kept = Object.keys(previous ?? {}).filter(key => !(key in entry));
	updated = [...updated.filter(item => item.id !== entry.id), { ...previous, ...entry }];
	console.log(`${previous ? 'Replaced' : 'Added'} ${entry.id} (${entry.sizeKB} KB)${kept.length ? `, kept ${kept.join(', ')}` : ''}`);
}
updated.sort((a, b) => a.category.localeCompare(b.category) || a.name.localeCompare(b.name));
await writeFile(CATALOG, JSON.stringify(updated, null, '\t') + '\n');

// The same lines as add-asset.mjs's credits(); the heading names this pack's source too.
const lines = updated.map(item => `- **${item.name}** (\`${item.file}\`): "[${item.source.title}](${item.source.url})" by ` +
	`${item.source.authorUrl ? `[${item.source.author}](${item.source.authorUrl})` : item.source.author} on ${item.source.site}, ` +
	`licensed [${item.source.license}](${item.source.licenseUrl}).${item.source.extraCredit ? ` ${item.source.extraCredit}.` : ''} Compressed and rescaled for this project.`);
await writeFile(join(LIB, 'CREDITS.md'), '# Asset library credits\n\nThese models come from Sketchfab, Poly Haven and the ' +
	'Construction Site packs under the licences listed. Keep this file with them. Items generated in code ' +
	`(src/procedural.js) are part of this project.\n\n${lines.join('\n')}\n`);
console.log(`${staged.length} item(s) merged; the library now has ${updated.length} downloaded models.`);
