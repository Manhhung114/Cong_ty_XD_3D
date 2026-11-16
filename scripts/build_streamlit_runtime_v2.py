"""Bundle the trusted XD+MEP frontend as one inline JS classic script.

Purpose: Streamlit st.iframe(html) runs HTML/JS in its own trusted sandbox;
never rely on /app/static/*.js MIME types or data: ESM imports.
No upload documents, auth secrets, backend runtime files or untrusted HTML.
"""
from __future__ import annotations
import base64
import html as htmlmod
import json
import re
from pathlib import Path

IMPORT = re.compile(r'^\s*import\s*\{([^}]*)\}\s*from\s*[\'\"]([^\'\"]+)[\'\"]\s*;?',re.M)
EXPORT = re.compile(r'^\s*export\s+(?:(async)\s+)?(const|let|var|function|class)\s+([a-zA-Z_$][a-zA-Z_$0-9]*)',re.M)
CSS_LINK = re.compile(r'<link\s+rel="stylesheet"\s+href="\./([^"<>]+\.css)"\s*/?>')
ENTRY = re.compile(r'<script\s+type="module"\s+src="\./src/app\.js"\s*></script>')
ASSET = re.compile(r"(['\"])(\./assets/[^'\"\n]+\.(?:webp|png|jpg|jpeg|svg))\1")


def build(static: Path, *, role: str = 'member', nonce: str = '') -> str:
    static = Path(static).resolve()
    cache: dict[Path,str] = {}
    order: list[Path] = []
    visiting: set[Path] = set()
    def safe(path: Path):
        p=path.resolve()
        if not p.is_relative_to(static) or not p.is_file(): raise ValueError(f'Not public file: {path}')
        return p
    def module(path: Path):
        path=safe(path)
        if path in cache:return
        if path in visiting:raise ValueError(f'Circular dependency: {path}')
        visiting.add(path)
        src=path.read_text(encoding='utf8')
        imports=[]
        def dep_import(m):
            dep=safe(path.parent / m.group(2))
            if not dep.suffix=='.js': raise ValueError('Only relative JS imports supported')
            module(dep)
            pairs=[]
            for name in m.group(1).split(','):
                n=name.strip()
                if not n: continue
                if re.fullmatch(r'[a-zA-Z_$][\w$]*\s+as\s+[a-zA-Z_$][\w$]*',n):
                    a,b=re.split(r'\s+as\s+',n);pairs.append(a+':'+b)
                elif re.fullmatch(r'[a-zA-Z_$][\w$]*',n):pairs.append(n)
                else:raise ValueError(f'Unknown import syntax: {n}')
            req=str(dep.relative_to(static)).replace('\\','/')
            imports.append(req)
            return 'const {'+','.join(pairs)+'}=__require('+json.dumps(req)+');'
        src=IMPORT.sub(dep_import,src)
        if re.search(r'^\s*import\s',src,re.M): raise ValueError(f'Unhandled ESM import in {path}')
        names=[]
        def remove_export(m):
            names.append(m.group(3))
            return (('async ' if m.group(1) else '')+m.group(2)+' '+m.group(3))
        src=EXPORT.sub(remove_export,src)
        if re.search(r'^\s*export\s',src,re.M):raise ValueError(f'Unhandled ESM export in {path}')
        def inline_asset(m):
            p=safe(static/m.group(2).removeprefix('./'))
            mt={'svg':'image/svg+xml','png':'image/png','jpg':'image/jpeg','jpeg':'image/jpeg','webp':'image/webp'}[p.suffix.lower().lstrip('.')]
            return m.group(1)+'data:'+mt+';base64,'+base64.b64encode(p.read_bytes()).decode('ascii')+m.group(1)
        src=ASSET.sub(inline_asset,src)
        tail='\n'+''.join(f'__exports[{json.dumps(n)}]={n};\n' for n in names)
        cache[path]='function(__exports,__require){\n'+src+tail+'\n}'
        visiting.remove(path)
        order.append(path)
    module(static/'src/app.js')
    members=',\n'.join(json.dumps(str(p.relative_to(static)).replace('\\','/'))+':'+cache[p] for p in order)
    js='''(function(){\n"use strict";\nconst __registry={'''+members+'''};\nconst __cache=Object.create(null);\nfunction __require(id){if(Object.prototype.hasOwnProperty.call(__cache,id))return __cache[id];const factory=__registry[id];if(!factory)throw Error("Missing JS module: "+id);const exports={};__cache[id]=exports;factory(exports,__require);return exports;}\ntry{__require("src/app.js")}catch(err){console.error("XD MEP app startup error",err);const root=document.getElementById("body");if(root){root.textContent="Không thể khởi tạo ứng dụng. Xem nhật ký lỗi trình duyệt.";root.style.cssText="color:#ffcf9c;padding:20px;";} }\n})();'''
    page=(static/'index.html').read_text(encoding='utf8')
    def css(m):
        source=safe(static/m.group(1)).read_text(encoding='utf8')
        return '<style>\n'+source.replace('</style>','<\\/style>')+'\n</style>'
    page,cn=CSS_LINK.subn(css,page)
    if cn<1:raise ValueError('No CSS inlined')
    # This is necessary because iframe srcdoc uses parent origin and otherwise
    # relative JSON/doc URLs would resolve from / instead of /app/static/.
    if role not in ("admin", "member"):
        raise ValueError("Invalid server-side role")
    if nonce and not re.fullmatch(r"[A-Za-z0-9_-]{20,100}", nonce):
        raise ValueError("Invalid Drive bridge nonce")
    # Embed only *public* metadata/templates in the authenticated iframe:
    # static web serving is disabled so the full app is no longer accessible
    # without Streamlit's top-level st.login guard.
    resources = {}
    data_dir = static / "data"
    if data_dir.is_dir():
        for file in data_dir.rglob("*"):
            if file.is_file() and file.suffix.lower() in (".json", ".csv", ".txt"):
                path = safe(file)
                key = str(path.relative_to(static)).replace("\\", "/")
                resources[key] = path.read_text(encoding="utf-8")
    if sum(map(len, resources.values())) > 2_000_000:
        raise ValueError("Excessive size of public embedded catalog")
    resources_json = json.dumps(resources, ensure_ascii=False).replace("<", "\\u003c")
    role_json = json.dumps(role)
    nonce_json = json.dumps(nonce)
    bootstrap = """<script>
window.__xdAuthRole = """ + role_json + """;
window.__xdDriveNonce = """ + nonce_json + """;
const __xdEmbeddedResources = """ + resources_json + """;
const __xdOriginalFetch = window.fetch.bind(window);
function __xdResourceKey(raw) {
  if (typeof raw !== "string" || !raw.startsWith("./data/")) return "";
  return raw.slice(2);
}
window.fetch = function(request, options) {
  const raw = typeof request === "string" ? request : request?.url;
  const key = __xdResourceKey(raw);
  if (Object.prototype.hasOwnProperty.call(__xdEmbeddedResources, key)) {
    const txt = __xdEmbeddedResources[key];
    return Promise.resolve(new Response(txt, {status:200,
      headers:{"content-type":key.endsWith(".json")?"application/json":"text/plain;charset=utf-8"}}));
  }
  return __xdOriginalFetch(request, options);
};
document.addEventListener("click", function(event) {
  const a = event.target.closest("a[href^='./data/templates/']");
  if (!a) return;
  const key = a.getAttribute("href").slice(2);
  if (!Object.prototype.hasOwnProperty.call(__xdEmbeddedResources,key)) return;
  event.preventDefault();
  const blob = new Blob([__xdEmbeddedResources[key]],{type:"text/csv;charset=utf-8"});
  const uri=URL.createObjectURL(blob), link=document.createElement("a");
  link.href=uri; link.download=key.split("/").pop();
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(()=>URL.revokeObjectURL(uri),2000);
});
</script>"""
    page = page.replace("<head>", "<head>\n"+bootstrap, 1)

    js=js.replace('</script','<\\/script')
    page,ns=ENTRY.subn(lambda m:'<script>\n'+js+'\n</script>',page)
    if ns!=1:raise ValueError('App ESM entry not found')
    if re.search(r'<script[^>]+src=',page):raise ValueError('Unexpected external script')
    if 'data:text/javascript' in page:raise ValueError('Data URL import still present')
    return page

if __name__ == '__main__':
    import sys
    p=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).parent/'Cong_ty_XD_3D_Streamlit/static'
    s=build(p)
    out=Path(sys.argv[2]) if len(sys.argv)>2 else Path('/mnt/data/streamlit_fix_v2_inline.html')
    out.write_text(s,encoding='utf8')
    print('Built',out,len(s),'chars')