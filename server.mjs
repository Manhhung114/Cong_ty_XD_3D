import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const root=path.dirname(fileURLToPath(import.meta.url));
const port=Number(process.env.PORT||8766);
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.csv':'text/csv; charset=utf-8','.json':'application/json; charset=utf-8','.md':'text/plain; charset=utf-8','.svg':'image/svg+xml','.png':'image/png','.ico':'image/x-icon'};
const server=http.createServer((req,res)=>{
  try{
    const url=new URL(req.url,'http://localhost');
    const decoded=decodeURIComponent(url.pathname);
    const absolute=path.resolve(root,'.'+decoded);
    if(absolute!==root&&!absolute.startsWith(root+path.sep)){res.writeHead(403);res.end('Forbidden');return;}
    const filename=fs.existsSync(absolute)&&fs.statSync(absolute).isDirectory()?path.join(absolute,'index.html'):absolute;
    fs.readFile(filename,(err,data)=>{
      if(err){res.writeHead(err.code==='ENOENT'?404:500);res.end('File not found');return;}
      res.writeHead(200,{'Content-Type':types[path.extname(filename).toLowerCase()]||'application/octet-stream','X-Content-Type-Options':'nosniff','Cache-Control':'no-cache'});res.end(data);
    });
  }catch{res.writeHead(400);res.end('Bad request');}
});
server.listen(port,'127.0.0.1',()=>console.log(`MEP AI Company 3D: http://localhost:${port}`));
