const {chromium}=require('playwright'); const http=require('http'),fs=require('fs'),path=require('path');
const dir=__dirname;
const srv=http.createServer((q,s)=>{const f=path.join(dir,decodeURIComponent(q.url.split('?')[0]));fs.readFile(f,(e,d)=>{if(e){s.writeHead(404);return s.end();}s.writeHead(200,{'Content-Type':f.endsWith('.html')?'text/html':'application/octet-stream'});s.end(d);});}).listen(8765);
(async()=>{const b=await chromium.launch({args:['--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const p=await b.newPage({viewport:{width:1600,height:1000}});
p.on('console',m=>console.log('console:',m.text())); p.on('pageerror',e=>console.log('err',e));
for(const v of (process.argv[2]||'group,berry,berrytop,cloud,drop').split(',')){
  await p.goto(`http://localhost:8765/render.html?view=${v}`); await p.waitForFunction(()=>document.title==='done',null,{timeout:120000});
  await p.screenshot({path:path.join(dir,'mockups',`${v}.png`)}); console.log('wrote',v);}
await b.close(); srv.close();})();
