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


def build(static: Path) -> str:
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
    page=page.replace('<head>','<head>\n<base href="/app/static/">',1)
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