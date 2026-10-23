// Stream a model file out of the project's private Vercel Blob store.
//
//     GET /api/file?pathname=models/<hash>/<repo path>
//
// Only pathnames under models/ are served. Pathnames are content-addressed, so
// a response never changes and browsers may cache it for good.

import { get } from '@vercel/blob';

export async function GET(request) {
  const pathname = new URL(request.url).searchParams.get('pathname');
  if (!pathname || !pathname.startsWith('models/') || pathname.includes('..')) {
    return new Response('Bad pathname', { status: 400 });
  }

  const result = await get(pathname, {
    access: 'private',
    ifNoneMatch: request.headers.get('if-none-match') ?? undefined,
  });
  if (!result) return new Response('Not found', { status: 404 });

  const headers = {
    ETag: result.blob.etag,
    'Cache-Control': 'private, max-age=31536000, immutable',
  };
  if (result.statusCode === 304) return new Response(null, { status: 304, headers });

  const file = pathname.split('/').pop();
  return new Response(result.stream, {
    headers: {
      ...headers,
      'Content-Type': result.blob.contentType || 'application/octet-stream',
      'Content-Disposition': `inline; filename="${file.replace(/"/g, '')}"`,
      'X-Content-Type-Options': 'nosniff',
    },
  });
}
