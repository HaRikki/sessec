'use strict';
// Zero-dependency static file server for the cloned site (serves ./frontend). Start with: npm start
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, 'frontend');
const PORT = parseInt(process.env.PORT || '8080', 10);
const HOST = process.env.HOST || '0.0.0.0';

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.htm': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
  '.webp': 'image/webp', '.avif': 'image/avif', '.ico': 'image/x-icon', '.woff': 'font/woff', '.woff2': 'font/woff2',
  '.ttf': 'font/ttf', '.otf': 'font/otf', '.txt': 'text/plain; charset=utf-8', '.xml': 'application/xml; charset=utf-8',
  '.mp4': 'video/mp4', '.webm': 'video/webm', '.mp3': 'audio/mpeg', '.pdf': 'application/pdf', '.map': 'application/json',
};

function resolveFile(urlPath) {
  let rel;
  try { rel = decodeURIComponent(urlPath.split('?')[0].split('#')[0]); } catch (e) { return null; }
  const target = path.normalize(path.join(ROOT, rel));
  if (target !== ROOT && !target.startsWith(ROOT + path.sep)) return null; // block path traversal
  const candidates = [target, target + '.html', path.join(target, 'index.html')];
  for (const c of candidates) {
    try { if (fs.statSync(c).isFile()) return c; } catch (e) { /* try next */ }
  }
  return undefined;
}

const server = http.createServer((req, res) => {
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    res.writeHead(405, { Allow: 'GET, HEAD' });
    return res.end();
  }
  let file = resolveFile(req.url);
  let status = 200;
  if (file === null) { res.writeHead(400); return res.end('Bad request'); }
  if (file === undefined) {
    status = 404;
    file = path.join(ROOT, '404.html');
    if (!fs.existsSync(file)) { res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' }); return res.end('Not found'); }
  }
  const type = TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream';
  res.writeHead(status, { 'Content-Type': type, 'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'public, max-age=300' });
  if (req.method === 'HEAD') return res.end();
  fs.createReadStream(file).on('error', () => res.end()).pipe(res);
});

server.listen(PORT, HOST, () => console.log('Serving ' + ROOT + ' on http://' + HOST + ':' + PORT));
