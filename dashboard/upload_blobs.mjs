#!/usr/bin/env node
// Upload the model files listed in site/blob-manifest.json to the project's
// private Vercel Blob store, then remove the manifest from the site.
//
//     node dashboard/upload_blobs.mjs     # after build_site.py, with BLOB_READ_WRITE_TOKEN set
//
// Pathnames are content-addressed (models/<sha256 prefix>/<repo path>), so a
// file already in the store is skipped and a changed file uploads under a new
// pathname. Old versions are left in place: other branches' previews may still
// point at them.

import { createReadStream } from 'node:fs';
import { readFile, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { list, put } from '@vercel/blob';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MANIFEST = path.join(ROOT, 'site', 'blob-manifest.json');
const CONCURRENCY = 4;
const MULTIPART_OVER = 50e6;

const uploads = JSON.parse(await readFile(MANIFEST, 'utf8'));

const existing = new Set();
let cursor;
do {
  const page = await list({ prefix: 'models/', cursor, limit: 1000 });
  for (const b of page.blobs) existing.add(b.pathname);
  cursor = page.hasMore ? page.cursor : undefined;
} while (cursor);

const todo = uploads.filter(u => !existing.has(u.pathname));
const mb = n => (n / 1e6).toFixed(1);
console.log(`blob: ${uploads.length - todo.length} already stored, uploading ${todo.length} ` +
            `(${mb(todo.reduce((s, u) => s + u.size, 0))} MB)`);

let next = 0;
async function worker() {
  while (next < todo.length) {
    const u = todo[next++];
    await put(u.pathname, createReadStream(path.join(ROOT, u.path)), {
      access: 'private',
      addRandomSuffix: false,
      allowOverwrite: true,
      multipart: u.size > MULTIPART_OVER,
    });
    console.log(`  ${u.path} (${mb(u.size)} MB)`);
  }
}
await Promise.all(Array.from({ length: CONCURRENCY }, worker));

await rm(MANIFEST);
