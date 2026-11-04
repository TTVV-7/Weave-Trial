// Every Construction Site pack model works in the app: it has a card in the library under its
// category, it loads with no page error, and placed in the scene it stands on its base at the size
// on its card. Run: node --test scripts/test-construction-ui.mjs
// Needs Playwright with Chromium (npm i -D playwright && npx playwright install chromium).
// For the Neptune twin's scripts/ folder; added with the Construction Site packs.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { after, before, test } from 'node:test';
import { startVite } from './worker-harness.mjs';

const require = createRequire( import.meta.url );
const PORT = Number( process.env.TEST_VITE_PORT ) || 5199;
const catalog = JSON.parse( readFileSync( new URL( '../public/library/library.json', import.meta.url ), 'utf8' ) );
const PACK = catalog.filter( item => item.source?.site === 'Construction Site packs' );

let vite, base, browser, page;
const errors = [];

before( async () => {

	const { chromium } = require( 'playwright' );
	vite = await startVite( PORT );
	base = vite.base;
	browser = await chromium.launch( { args: [ '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader' ] } );
	page = await browser.newPage( { viewport: { width: 1280, height: 800 } } );
	page.on( 'pageerror', e => errors.push( String( e ) ) );
	await page.route( '**/*', route => {

		const url = route.request().url();
		return url.startsWith( base ) || url.startsWith( 'data:' ) || url.startsWith( 'blob:' ) ? route.continue() : route.abort();

	} );
	await page.goto( `${ base }/?prompt` );
	await page.click( '#skip' );
	await page.waitForFunction( () => window.twin?.sidebar && window.twin.layout );

} );

after( async () => {

	await browser?.close();
	vite?.stop();

} );

test( 'the pack is in the library', () => {

	assert.ok( PACK.length > 0, 'no Construction Site pack items in library.json' );

} );

test( 'each model has a card under its category', async () => {

	const found = await page.evaluate( ids => ids.filter( id => document.querySelector( `[data-item="${ id }"]` ) ), PACK.map( i => i.id ) );
	assert.deepEqual( found.sort(), PACK.map( i => i.id ).sort() );

} );

test( 'each model loads, stands on its base and matches its card', async () => {

	const measured = await page.evaluate( async ids => {

		const { models } = window.twin;
		const library = await import( '/src/library.js' );
		const items = await library.loadLibrary();
		// the copy of three.js Vite pre-bundled for the app, else the package's own build
		const three = await import( '/node_modules/.vite/deps/three.js' ).catch( () => import( '/node_modules/three/build/three.module.js' ) );
		const { Box3, Vector3 } = three;
		const out = [];
		for ( const [ i, id ] of ids.entries() ) {

			const item = items.find( it => it.id === id );
			const entry = await models.load( library.itemConfig( item, { east: ( i % 8 ) * 25, north: Math.floor( i / 8 ) * 25, heading: 0 } ) );
			entry.pivot.updateMatrixWorld( true );
			const box = new Box3().setFromObject( entry.pivot );
			const size = box.getSize( new Vector3() );
			const base = box.min.y - entry.pivot.position.y;
			out.push( { id, size: [ size.x, size.y, size.z ], base, dims: item.dimensions } );

		}

		return out;

	}, PACK.map( i => i.id ) );
	const wrong = [];
	for ( const { id, size: [ x, y, z ], base, dims } of measured ) {

		const plan = [ Math.max( x, z ), Math.min( x, z ) ];
		const card = [ Math.max( dims.length, dims.width ), Math.min( dims.length, dims.width ) ];
		const off = ( a, b ) => Math.abs( a - b ) > Math.max( 0.05, 0.05 * b );
		if ( off( plan[ 0 ], card[ 0 ] ) || off( plan[ 1 ], card[ 1 ] ) || off( y, dims.height ) )
			wrong.push( `${ id }: placed ${ plan[ 0 ].toFixed( 2 ) } x ${ plan[ 1 ].toFixed( 2 ) } x ${ y.toFixed( 2 ) } m, card ${ card[ 0 ] } x ${ card[ 1 ] } x ${ dims.height }` );
		if ( Math.abs( base ) > 0.02 ) wrong.push( `${ id }: base ${ base.toFixed( 3 ) } m off the ground` );

	}

	assert.deepEqual( wrong, [] );
	assert.deepEqual( errors, [], 'page errors while loading the pack' );

} );
