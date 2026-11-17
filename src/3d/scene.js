import {OFFICE_ROOMS,AGENTS,FLOOR_HEIGHT,visibleDepartments,agentOffice,roomAgents,seatOffset} from '../core/config.js';
import {agentEvidence} from '../core/agent_live.js';
const TAU=Math.PI*2;
const norm=a=>{let l=Math.hypot(...a)||1;return a.map(n=>n/l)};
const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
function mul(a,b){const o=new Float32Array(16);for(let c=0;c<4;c++)for(let r=0;r<4;r++)for(let k=0;k<4;k++)o[c*4+r]+=a[k*4+r]*b[c*4+k];return o;}
function perspective(fov,aspect,n,f){const v=1/Math.tan(fov/2);return new Float32Array([v/aspect,0,0,0,0,v,0,0,0,0,(f+n)/(n-f),-1,0,0,2*f*n/(n-f),0]);}
function lookAt(e,t){const z=norm(e.map((v,i)=>v-t[i])),x=norm(cross([0,1,0],z)),y=cross(z,x);return new Float32Array([x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,e),-dot(y,e),-dot(z,e),1]);}
function model(x,y,z,sx,sy,sz,r=0){const c=Math.cos(r),s=Math.sin(r);return new Float32Array([c*sx,0,-s*sx,0,0,sy,0,0,s*sz,0,c*sz,0,x,y,z,1]);}
function hex(h){h=h.replace('#','');return [(parseInt(h.slice(0,2),16)||0)/255,(parseInt(h.slice(2,4),16)||0)/255,(parseInt(h.slice(4,6),16)||0)/255];}
function cube(){const p=[],n=[];const sides=[[[1,0,0],[[.5,-.5,.5],[.5,-.5,-.5],[.5,.5,-.5],[.5,.5,.5]]],[[-1,0,0],[[-.5,-.5,-.5],[-.5,-.5,.5],[-.5,.5,.5],[-.5,.5,-.5]]],[[0,1,0],[[-.5,.5,.5],[.5,.5,.5],[.5,.5,-.5],[-.5,.5,-.5]]],[[0,-1,0],[[-.5,-.5,-.5],[.5,-.5,-.5],[.5,-.5,.5],[-.5,-.5,.5]]],[[0,0,1],[[.5,-.5,.5],[-.5,-.5,.5],[-.5,.5,.5],[.5,.5,.5]]],[[0,0,-1],[[-.5,-.5,-.5],[.5,-.5,-.5],[.5,.5,-.5],[-.5,.5,-.5]]]];for(const [normal,verts] of sides){for(const i of [0,1,2,0,2,3]){p.push(...verts[i]);n.push(...normal);}}return {p:new Float32Array(p),n:new Float32Array(n),count:p.length/3};}
function sphere(){const p=[],n=[];const ring=9,seg=12;for(let j=0;j<ring;j++){const a0=j*Math.PI/ring,a1=(j+1)*Math.PI/ring;for(let i=0;i<seg;i++){const b0=i*TAU/seg,b1=(i+1)*TAU/seg;function point(a,b){return [Math.sin(a)*Math.cos(b),Math.cos(a),Math.sin(a)*Math.sin(b)];}const v=[point(a0,b0),point(a1,b0),point(a1,b1),point(a0,b1)];for(const k of [0,1,2,0,2,3]){p.push(...v[k]);n.push(...v[k]);}}}return {p:new Float32Array(p),n:new Float32Array(n),count:p.length/3};}
function shader(gl,type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
function program(gl){const v=shader(gl,gl.VERTEX_SHADER,`attribute vec3 aPos; attribute vec3 aNorm; uniform mat4 uMVP; uniform mat4 uModel; uniform float uRot; varying vec3 vNorm; varying vec3 vWorld; void main(){gl_Position=uMVP*vec4(aPos,1.); float c=cos(uRot),s=sin(uRot);vNorm=normalize(vec3(c*aNorm.x+s*aNorm.z,aNorm.y,-s*aNorm.x+c*aNorm.z));vWorld=(uModel*vec4(aPos,1.)).xyz;}`);const f=shader(gl,gl.FRAGMENT_SHADER,`precision mediump float; uniform vec3 uColor; uniform float uEmissive; varying vec3 vNorm; varying vec3 vWorld; void main(){float lum=max(dot(normalize(vNorm),normalize(vec3(-.48,.9,1.1))),0.);float shade=.47+.53*lum;float depth=clamp((vWorld.y+1.)/5.,0.,1.);vec3 outColor=uColor*(shade+.045*depth)+uColor*uEmissive;gl_FragColor=vec4(outColor,1.);}`);const p=gl.createProgram();gl.attachShader(p,v);gl.attachShader(p,f);gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));return p;}
function floorSpans(rooms){
 const spans=new Map();
 for(const {floor,position:[x]} of rooms){
  const span=spans.get(floor)||{left:-13.9,right:13.9};
  span.left=Math.min(span.left,x-4.45);
  span.right=Math.max(span.right,x+4.45);
  spans.set(floor,span);
 }
 return Array.from(spans,([floor,{left,right}])=>({floor,left,right,center:(left+right)/2,width:right-left}));
}

export class Office3D{
 constructor(container,options={}){this.container=container;this.options=options;this.state=options.getState;this.view=options.view||'all';this.rooms=visibleDepartments(this.view);this.floorSpans=floorSpans(this.rooms);this.specialistDistance=this.rooms.some(room=>room.agentId)?10:0;this.selected=this.state()?.selectedDept||OFFICE_ROOMS[0].id;this.yaw=.55;this.pitch=.68;this.distance=(this.view==='all'?52:37)+this.specialistDistance;this.focusY=this.view==='all'?FLOOR_HEIGHT*.81:this.view==='construction'?FLOOR_HEIGHT:0;this.preset='isometric';this.quality='auto';this.mobile=matchMedia('(max-width: 750px)').matches;this.drag=false;this.down=null;this.frame=0;this.dead=false;this.dpr=Math.min(window.devicePixelRatio||1,this.mobile?1.15:1.6);this.canvas=document.createElement('canvas');this.canvas.className='office-canvas';container.append(this.canvas);this.overlay=document.createElement('div');this.overlay.className='world-overlay';container.append(this.overlay);this.labels=OFFICE_ROOMS.map(d=>{const el=document.createElement('button');el.type='button';el.className='world-label';el.dataset.officeRoom=d.id;el.setAttribute('aria-label','Chọn phòng '+d.name);el.innerHTML=`<span class="world-label-dot" style="background:${d.color}"></span><span>${d.short}</span>`;el.title=d.name;el.onclick=()=>this.select(d.id);this.overlay.append(el);return el;});try{this.gl=this.canvas.getContext('webgl',{antialias:true,alpha:false,powerPreference:'default'});if(!this.gl)throw Error('Thiết bị không hỗ trợ WebGL');this._init();}catch(e){this.failed=true;this.canvas.remove();this.overlay.remove();this.fallbackRender();return;}this.setQuality('auto');this._bind();this.resizeObserver=new ResizeObserver(()=>this.resize());this.resizeObserver.observe(container);this.resize();this._animate=this._animate.bind(this);this._animate();}
 _init(){const g=this.gl;this.program=program(g);g.useProgram(this.program);this.loc={pos:g.getAttribLocation(this.program,'aPos'),norm:g.getAttribLocation(this.program,'aNorm'),mvp:g.getUniformLocation(this.program,'uMVP'),model:g.getUniformLocation(this.program,'uModel'),rot:g.getUniformLocation(this.program,'uRot'),color:g.getUniformLocation(this.program,'uColor'),emissive:g.getUniformLocation(this.program,'uEmissive')};this.meshes={cube:cube(),sphere:sphere()};for(const m of Object.values(this.meshes)){m.position=g.createBuffer();g.bindBuffer(g.ARRAY_BUFFER,m.position);g.bufferData(g.ARRAY_BUFFER,m.p,g.STATIC_DRAW);m.normal=g.createBuffer();g.bindBuffer(g.ARRAY_BUFFER,m.normal);g.bufferData(g.ARRAY_BUFFER,m.n,g.STATIC_DRAW);}g.enable(g.DEPTH_TEST);g.clearColor(.62,.82,.92,1);}
 _bind(){let downPt=null;this.canvas.addEventListener('pointerdown',e=>{this.canvas.setPointerCapture?.(e.pointerId);downPt={x:e.clientX,y:e.clientY,yaw:this.yaw,pitch:this.pitch};});this.canvas.addEventListener('pointermove',e=>{if(!downPt)return;const dx=e.clientX-downPt.x,dy=e.clientY-downPt.y;this.yaw=downPt.yaw-dx*.009;this.pitch=Math.max(.35,Math.min(1.36,downPt.pitch+dy*.007));});this.canvas.addEventListener('pointerup',e=>{if(!downPt)return;const distance=Math.hypot(e.clientX-downPt.x,e.clientY-downPt.y);downPt=null;if(distance<7)this.pick(e);});this.canvas.addEventListener('wheel',e=>{e.preventDefault();this.distance=Math.max(22,Math.min(69,this.distance+Math.sign(e.deltaY)*2.7));},{passive:false});this.canvas.addEventListener('dblclick',()=>this.resetCamera());this.canvas.addEventListener('pointercancel',()=>{downPt=null});this.canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();this.contextLost=true;});this.canvas.addEventListener('webglcontextrestored',()=>{this.contextLost=false;this._init();this.resize();});}
 resetCamera(){this.setCameraPreset('isometric');if(this.failed){this.svgZoom=1;this.fallbackRender();}}
 setCameraPreset(preset='isometric'){this.preset=preset;const y=this.view==='construction'?FLOOR_HEIGHT:this.view==='mep'?0:FLOOR_HEIGHT*.81;const presets={isometric:[.65,.72,this.view==='all'?52:37,y],front:[0,.32,this.view==='all'?56:43,y],top:[.65,1.31,this.view==='all'?52:41,y+1.5],mep:[.65,.68,35,0],construction:[.65,.68,35,FLOOR_HEIGHT]};const [yaw,pitch,distance,focusY]=presets[preset]||presets.isometric;this.yaw=yaw;this.pitch=pitch;this.distance=distance+this.specialistDistance;this.focusY=focusY;}
 zoomBy(step){this.distance=Math.max(22,Math.min(76,this.distance+step));}
 setQuality(value){this.quality=value==='low'?'low':value==='high'?'high':'auto';this.lowDetail=this.quality==='low'||(this.quality==='auto'&&this.mobile);this.dpr=Math.min(window.devicePixelRatio||1,this.lowDetail?1.1:1.65);this.resize();}
 select(dept){this.selected=dept;this.options.onSelect?.(dept);if(this.failed)this.fallbackRender();else this.updateLabels();}
 resize(){if(!this.gl||this.dead)return;const w=this.container.clientWidth,h=this.container.clientHeight;this.width=w;this.height=h;this.canvas.width=Math.max(1,Math.round(w*this.dpr));this.canvas.height=Math.max(1,Math.round(h*this.dpr));this.gl.viewport(0,0,this.canvas.width,this.canvas.height);}
 _camera(){const r=this.distance;this.eye=[r*Math.cos(this.pitch)*Math.sin(this.yaw),this.focusY+r*Math.sin(this.pitch),r*Math.cos(this.pitch)*Math.cos(this.yaw)];this.forward=norm(this.eye.map((v,i)=>(i===1?this.focusY:0)-v));this.right=norm(cross(this.forward,[0,1,0]));this.up=cross(this.right,this.forward);this.fov=.68;this.aspect=(this.width||1)/(this.height||1);this.vp=mul(perspective(this.fov,this.aspect,.1,140),lookAt(this.eye,[0,this.focusY,0]));}
 project(p){const q=p.map((v,i)=>v-this.eye[i]);const z=dot(q,this.forward);if(z<.1)return null;const k=Math.tan(this.fov/2);return {x:this.width/2+dot(q,this.right)/z/k/this.aspect*this.width/2,y:this.height/2-dot(q,this.up)/z/k*this.height/2,z};}
 pick(e){const rect=this.canvas.getBoundingClientRect();const x=e.clientX-rect.left,y=e.clientY-rect.top;let nearest={dist:29,agent:null};const visible=this.rooms;const ids=new Set(visible.map(d=>d.id));for(const a of AGENTS.filter(a=>ids.has(agentOffice(a)))){const p=this.agentPos(a);const proj=this.project([p[0],p[1]+2.2,p[2]]);if(proj){const dis=Math.hypot(proj.x-x,proj.y-y);if(dis<nearest.dist)nearest={dist:dis,agent:a};}}if(nearest.agent){this.select(agentOffice(nearest.agent));this.options.onAgent?.(nearest.agent);return;}const nx=(x/this.width*2-1)*this.aspect*Math.tan(this.fov/2),ny=(1-y/this.height*2)*Math.tan(this.fov/2);const ray=norm(this.forward.map((v,i)=>v+this.right[i]*nx+this.up[i]*ny));if(ray[1]>=0)return;const floors=[...new Set(visible.map(d=>d.floor))].sort((a,b)=>b-a);for(const floor of floors){const base=floor*FLOOR_HEIGHT;const t=(base-this.eye[1])/ray[1];if(t<=0)continue;const wx=this.eye[0]+t*ray[0],wz=this.eye[2]+t*ray[2];const found=visible.find(d=>d.floor===floor&&Math.abs(d.position[0]-wx)<2.95&&Math.abs(d.position[1]-wz)<3.22);if(found){this.select(found.id);return;}}}
 agentPos(a){const room=agentOffice(a),d=OFFICE_ROOMS.find(v=>v.id===room);
 const occupants=roomAgents(room),index=occupants.findIndex(q=>q.id===a.id);
 return [d.position[0]+seatOffset(index,occupants.length),d.floor*FLOOR_HEIGHT,d.position[1]+.7];}

 draw(type,x,y,z,sx,sy,sz,color,rot=0,emissive=0){const g=this.gl,l=this.loc,m=this.meshes[type],mod=model(x,y,z,sx,sy,sz,rot);g.bindBuffer(g.ARRAY_BUFFER,m.position);g.vertexAttribPointer(l.pos,3,g.FLOAT,false,0,0);g.enableVertexAttribArray(l.pos);g.bindBuffer(g.ARRAY_BUFFER,m.normal);g.vertexAttribPointer(l.norm,3,g.FLOAT,false,0,0);g.enableVertexAttribArray(l.norm);g.uniformMatrix4fv(l.mvp,false,mul(this.vp,mod));g.uniformMatrix4fv(l.model,false,mod);g.uniform1f(l.rot,rot);g.uniform3fv(l.color,hex(color));g.uniform1f(l.emissive,emissive);g.drawArrays(g.TRIANGLES,0,m.count);}
 box(x,y,z,sx,sy,sz,color,r=0,em=0){this.draw('cube',x,y,z,sx,sy,sz,color,r,em);}
 ball(x,y,z,r,color,em=0){this.draw('sphere',x,y,z,r,r,r,color,0,em);}
 office(t){const pulse=.5+.5*Math.sin(t*2.5);
 for(const {floor,left,right,center,width} of this.floorSpans){
  const y=floor*FLOOR_HEIGHT;
  this.box(center,y-.44,0,width-.2,.49,14.65,'#aecfdf');
  this.box(center,y-.15,0,width,.08,14.9,'#ecf6fd');
  this.box(center,y-.37,7.4,width+.2,.32,.15,'#4989ad');
  this.box(center,y+.48,-7.28,width,1.5,.16,'#4079a4');
  for(let gx=left+.9;gx<=right-.9;gx+=1.8)this.box(gx,y-.08,0,.018,.012,13.8,'#d6e8f1');
  for(let gz=-7;gz<=7;gz+=1.8)this.box(center,y-.08,gz,width-.6,.012,.018,'#d6e8f1');
 }
 for(const d of this.rooms){const [x,z]=d.position,y=d.floor*FLOOR_HEIGHT,active=this.selected===d.id;this.box(x,y-.06,z,5.85,.12,6.30,active?'#d5f1f5':'#edf8fe');this.box(x,y-.06,z-3.07,5.85,.07,.11,d.color);this.box(x,y-.05,z+3.10,5.85,.08,.09,d.color);this.box(x-2.94,y+.48,z,.15,1.00,6.22,'#588fb1');this.box(x+2.94,y+.48,z,.15,1.00,6.22,'#588fb1');this.box(x,y+.68,z-3.10,5.85,1.55,.15,'#3e7ca6');this.box(x,y+1.20,z-3.02,2.35,.14,.09,d.color,0,.30);this.box(x-2.60,y+1.30,z-2.86,.20,.37,.15,'#ebf5fd');
 // Back-wall double display, charts and overhead warm light.
 this.box(x,y+1.57,z-2.96,1.62,.88,.09,'#1b4b69');
 this.box(x,y+1.57,z-2.90,1.48,.73,.03,'#2c9bcc',0,.18);
 for(let i=0;i<5;i++)this.box(x-.56+i*.28,y+1.36+i*.09,z-2.869,.15,.03,.013,i%2?'#6bf0db':'#dcfaff',0,.45);
 this.box(x+1.32,y+1.58,z-2.87,.43,.65,.025,'#c7f5ff',0,.2);
 this.box(x+1.32,y+1.52,z-2.845,.29,.05,.012,d.color,0,.3);
 this.ball(x+.45,y+2.77,z-1.85,.17,'#fff2c7',.35);

 this.box(x,y+2.86,z-1.85,2.8,.08,.18,'#dff5ff',0,.13);
 const members=roomAgents(d.id);members.forEach((a,i)=>{const px=x+seatOffset(i,members.length),pz=z+.7;this.desk(px,pz,d.color,y);this.avatar(a,px,pz,t,y);});
 this.box(x+2.14,y+.55,z-2.36,.8,1.12,.50,'#bdd3df');this.box(x+2.14,y+1.14,z-2.38,.82,.06,.55,'#f4faff');this.box(x-2.17,y+.29,z-2.4,.38,.5,.38,'#e0e8e1');this.ball(x-2.17,y+.73,z-2.4,.42,'#4c9a7e');this.ball(x-1.94,y+.94,z-2.55,.24,'#76c3a7');
 if(d.division==='construction'){// Construction props: material stacks and miniature structural frame
  this.box(x+2.18,y+.20,z+2.22,.65,.38,.52,'#d1ac78');this.box(x+2.18,y+.40,z+2.22,.6,.10,.48,'#f5d4a4');
  if(d.id==='xd_site'||d.id==='xd_safety')this.box(x-2.18,y+.34,z+2.30,.50,.23,.45,'#f0b93c');
 }
 if(active)this.box(x,y-.02,z,5.75,.025,6.2,d.color,0,.06+pulse*.10);
 }
 // V5.2: real three-storey cutaway. The top level is a shared executive/meeting suite,
 // not a new AI agent and not a duplicate of any technical department.
 if(this.view==='all'){
  const y=FLOOR_HEIGHT*2;
  this.box(0,y-.45,-2,16,.4,8.65,'#bed8e9');this.box(0,y-.18,-2,16.1,.11,8.8,'#f3fbff');
  this.box(0,y+1.25,-6.3,16,3,.15,'#39769e');
  this.box(-7.95,y+1.2,-2,.14,2.7,8.6,'#6ca8c8');this.box(7.95,y+1.2,-2,.14,2.7,8.6,'#6ca8c8');
  this.box(0,y+2.55,-6.08,6.0,.18,.09,'#80edfa',0,.38);
  this.box(0,y+1.8,-6.13,3.75,1.0,.1,'#0d395f');this.box(0,y+1.8,-6.05,3.44,.79,.025,'#2b9bcd',0,.6);
  for(let i=0;i<7;i++)this.box(-1.3+i*.44,y+1.68,-6.01,.17,.14+i*.06,.017,i%2?'#a4f7e9':'#c5f9ff',0,.35);
  this.box(0,y+.95,-2.7,3.8,.18,1.8,'#eef7fb');this.box(0,y+.47,-2.7,3.4,.76,1.35,'#bdd4e1');
  for(const x of [-1.1,0,1.1])for(const z of [-.95,-4.45]){
   this.box(x,y+.55,z,.60,.15,.59,'#246c9a');this.box(x,y+.83,z+(z>-2?-.32:.32),.65,.8,.12,'#2a77b0');
  }
  for(const x of [-6.4,6.4]){this.box(x,y+.48,-5,.58,.85,.55,'#e8f2e9');this.ball(x,y+1.22,-5,.60,'#4eaa87');this.ball(x+.25,y+1.6,-5.1,.36,'#78c5a4');}
  for(let i=0;i<5;i++)this.box(-6+i*3,y+3.0,-2,.72,.07,.23,'#f3eecc',0,.2);
 }
 // Shared glass-like digital board with building model at the front of both offices.
 if(this.view==='all'){this.box(0,1.72,7.64,5.7,3.35,.07,'#36b4d7',0,.55);this.box(0,1.72,7.69,4.9,2.73,.04,'#0c527d',0,.36);for(let i=0;i<5;i++)this.box(-1.82+i*.72,1.19+i*.26,7.74,.42,.1,.04,'#76e4f5',0,.52);this.box(.9,1.67,7.78,1.4,1.1,.07,'#82dbef',0,.48);}
 }
 desk(x,z,color,y=0){
  // Light desks, workstation equipment and adjustable chairs in the source image's style.
  this.box(x,y+1.06,z-.24,1.98,.13,1.00,'#eff9ff');
  this.box(x,y+.99,z-.24,2.02,.065,1.06,'#c6dde9');
  for(const dx of [-.85,.85])for(const dz of [-.53,.12])this.box(x+dx,y+.51,z+dz,.09,.95,.10,'#a9c6d5');
  this.box(x-.78,y+.54,z-.30,.36,.72,.70,'#e7eff6');
  this.box(x-.78,y+.54,z-.66,.38,.026,.72,'#9cbacb');
  // Monitor, luminous UI, bezel, stand, keyboard, mouse.
  this.box(x,y+1.55,z-.66,1.00,.59,.070,'#11324d');
  this.box(x,y+1.56,z-.614,.86,.44,.025,'#4cb6d3',0,.48);
  this.box(x-.20,y+1.64,z-.596,.24,.05,.012,'#c7faff',0,.65);
  this.box(x+.23,y+1.47,z-.593,.26,.06,.013,'#7bf8ea',0,.55);
  this.box(x,y+1.20,z-.66,.065,.25,.07,'#7193ac');
  this.box(x,y+1.13,z-.49,.48,.035,.22,'#bfd6e4');
  this.box(x-.04,y+1.12,z-.12,.68,.028,.22,'#8eafc4');
  this.ball(x+.65,y+1.12,z-.12,.065,'#6d91ad');
  // Chair with backrest, castor base and armrests.
  this.box(x,y+.57,z+1.06,.68,.15,.67,'#245d92');
  this.box(x,y+.84,z+1.42,.69,.73,.12,'#2c73b0');
  this.box(x,y+.22,z+1.03,.08,.57,.08,'#244a69');
  this.box(x,y+.12,z+1.05,.85,.065,.14,'#2e6589');
  this.box(x-.42,y+.73,z+1.04,.07,.13,.54,'#d5e8f2');
  this.box(x+.42,y+.73,z+1.04,.07,.13,.54,'#d5e8f2');
 }
 avatar(a,x,z,t,y=0){
  // A task marked "working" does not establish that the AI itself is running.
  const status=agentEvidence(this.options.getCloud?.(),a.id);
  const doing=['started_unconfirmed','running'].includes(status.state);
  const review=status.state==='failed';
  const complete=status.state==='completed';
  const bob=doing?.03*Math.sin(t*3.1+a.id.length):.01*Math.sin(t*1.1);
  const shirts=['#2b93d0','#f06997','#2a9e9b','#567db9','#eaa15c','#6476b7'];
  const shirt=doing?'#319eaf':review?'#cf5d64':complete?'#32a483':shirts[(a.id.charCodeAt(0)+a.id.length)%shirts.length];
  const skin=(a.id.charCodeAt(0)%3===0)?'#d8a17d':'#f0c6a5';
  // Legs and shoes, a seated employee facing a glowing desk display.
  this.box(x-.19,y+.38,z+1.10,.21,.68,.28,'#2d516d');
  this.box(x+.19,y+.38,z+1.10,.21,.68,.28,'#2d516d');
  this.box(x-.20,y+.09,z+.90,.28,.11,.44,'#1f3f5c');
  this.box(x+.20,y+.09,z+.90,.28,.11,.44,'#1f3f5c');
  this.box(x,y+1.07+bob,z+1.03,.68,.81,.47,shirt);
  this.box(x,y+1.43+bob,z+1.01,.79,.16,.49,shirt);
  this.ball(x,y+1.86+bob,z+1.04,.35,skin);
  this.ball(x,y+2.05+bob,z+.99,.29,'#263e52');
  this.box(x,y+2.03+bob,z+1.24,.44,.13,.14,'#273d4e');
  this.ball(x-.11,y+1.85+bob,z+1.35,.027,'#1b384d');
  this.ball(x+.11,y+1.85+bob,z+1.35,.027,'#1b384d');
  // Two articulated arms typing or reading a drawing.
  this.box(x-.40,y+1.12+bob,z+.78,.20,.50,.27,shirt,doing?-.22:0);
  this.box(x+.40,y+1.12+bob,z+.78,.20,.50,.27,shirt,doing?.22:0);
  this.box(x-.44,y+.90+bob,z+.48,.16,.18,.38,skin,doing?.22:0);
  this.box(x+.44,y+.90+bob,z+.48,.16,.18,.38,skin,doing?-.22:0);
  this.ball(x,y+2.44+bob,z+.96,.13,doing?'#4cf2ce':review?'#ff718a':complete?'#6affc9':'#8fadc6',doing?.78:.22);
 }

 fallbackRender(){
  // SVG isometric fallback: preserves room interaction if WebGL is disabled.
  this.svgZoom=this.svgZoom||.97;
  const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&quot;'}[c]));
  const P=(x,z,y=0)=>[500+(x-z)*15.4,520+(x+z)*7.2-y*37];
  const pts=arr=>arr.map(p=>P(...p).map(n=>n.toFixed(1)).join(',')).join(' ');
  const polygon=(arr,color,stroke='#19394a',alpha=1)=>`<polygon points="${pts(arr)}" fill="${color}" fill-opacity="${alpha}" stroke="${stroke}" stroke-width=".9"/>`;
  const block=(x,z,y,w,d,h,top='#3b6974',front='#234556',right='#1b3a4c')=>{
    const a=[x-w/2,z-d/2],b=[x+w/2,z-d/2],c=[x+w/2,z+d/2],f=[x-w/2,z+d/2];
    return polygon([[...f,y],[...c,y],[...c,y+h],[...f,y+h]],front)+polygon([[...c,y],[...b,y],[...b,y+h],[...c,y+h]],right)+polygon([[...a,y+h],[...b,y+h],[...c,y+h],[...f,y+h]],top);
  };
  const rooms=[...this.rooms].sort((a,b)=>a.floor-b.floor||(a.position[0]+a.position[1])-(b.position[0]+b.position[1]));
  let markup=`<svg class="office-svg-fallback" viewBox="0 0 1000 700" role="img" aria-label="Văn phòng công ty MEP và Xây dựng dạng phối cảnh isometric. Chạm vào phòng để xem công việc."><defs><radialGradient id="bgSVG"><stop stop-color="#1c4254"/><stop offset="1" stop-color="#0b1c2b"/></radialGradient><filter id="glowSVG"><feGaussianBlur stdDeviation="4" /></filter></defs><rect width="1000" height="700" fill="url(#bgSVG)"/><g transform="translate(500 300) scale(${this.svgZoom}) translate(-500 -300)">`;
  for(const {floor,center,width} of [...this.floorSpans].sort((a,b)=>a.floor-b.floor))markup+=block(center,0,floor*FLOOR_HEIGHT-.72,width-.3,14.6,.32,'#d3edf8','#7daec7','#b0d5e7');
  const roomLabels=[];
  for(const d of rooms){const [x,z]=d.position,y=d.floor*FLOOR_HEIGHT;const active=d.id===this.selected;
    markup+=`<g class="svg-room" data-svg-dept="${d.id}" tabindex="0" role="button" aria-label="${esc(d.name)}">`;
    markup+=block(x,z,y-.3,5.8,6.1,.22,active?'#b9ecf0':'#e5f2fb','#77b4cc','#a6d5e6');
    markup+=block(x,z-2.97,y-.04,5.8,.10,1.25,'#7aafcc','#4e88a8','#417496');
    markup+=block(x-2.85,z,y-.04,.10,6.0,1.2,'#83b5cf','#619ab9','#497b9c');
    markup+=block(x,z-2.84,y+1.23,3.1,.10,.08,d.color,d.color,d.color);
    const members=roomAgents(d.id);
    members.forEach((a,i)=>{const ax=x+seatOffset(i,members.length),az=z+.50;
      markup+=block(ax,az,y,1.65,.94,.85,'#eef8fd','#87acc4','#6793b0');
      markup+=block(ax,az-.36,y+.86,.82,.12,.42,d.color,'#245477','#28618c');
      const [bx,by]=P(ax,az+1.0,y+1.05),[hx,hy]=P(ax,az+1.0,y+1.93);
      const working=agentEvidence(this.options.getCloud?.(),a.id).state==='started_unconfirmed';
      markup+=`<ellipse cx="${bx}" cy="${by+8}" rx="10" ry="15" fill="${working?'#40c3b3':'#6c8a9c'}" opacity=".84"/><circle cx="${hx}" cy="${hy}" r="8.7" fill="#e3b799" stroke="#f5ccaf" stroke-width="1.5"/><path d="M ${hx-7} ${hy-6} Q ${hx} ${hy-15} ${hx+7} ${hy-6}" fill="none" stroke="#2b3444" stroke-width="4"/>`;
      markup+=`<circle cx="${hx+12}" cy="${hy-12}" r="3.8" fill="${working?'#61e6bf':'#89a9bd'}" class="svg-pulse"/>`;
    });
    markup+=block(x+2,z-2.35,y,.75,.60,.90,'#aac5d5','#719ab2','#6288a3');
    const [tx,ty]=P(x,z-2.8,y+2.10);
    roomLabels.push(`<g data-svg-room-label="${d.id}" aria-hidden="true" cursor="pointer"><rect x="${tx-39}" y="${ty-12}" width="78" height="23" rx="5" fill="${active?'#113c41':'#102a38'}" stroke="${d.color}" stroke-width="1.4"/><circle cx="${tx-27}" cy="${ty-.5}" r="3" fill="${d.color}"/><text x="${tx+3}" y="${ty+4}" fill="#e8fbff" font-size="11" font-weight="700" text-anchor="middle">${esc(d.short)}</text></g>`);
    markup+=`</g>`;
  }
  markup+=roomLabels.join('');
  markup+=`</g><text x="28" y="676" fill="#83a9b8" font-size="12" letter-spacing=".6">SVG ISOMETRIC FALLBACK · CHỌN PHÒNG ĐỂ XEM NHIỆM VỤ</text></svg>`;
  let target=this.container.querySelector('.office-svg-fallback');
  if(target)target.outerHTML=markup;else this.container.insertAdjacentHTML('beforeend',markup);
  this.container.querySelectorAll('[data-svg-dept]').forEach(g=>{g.addEventListener('click',()=>this.select(g.getAttribute('data-svg-dept')));g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();this.select(g.getAttribute('data-svg-dept'));}});});
  this.container.querySelectorAll('[data-svg-room-label]').forEach(label=>{
    label.addEventListener('click',()=>this.select(label.getAttribute('data-svg-room-label')));
  });
  const hint=this.container.querySelector('.office-hint');if(hint)hint.textContent='Chế độ phối cảnh 3D dự phòng · Chạm chọn từng phòng';
  if(!this.fallbackWheelBound){this.container.addEventListener('wheel',e=>{if(!this.failed)return;e.preventDefault();this.svgZoom=Math.max(.75,Math.min(1.4,(this.svgZoom||1)+Math.sign(-e.deltaY)*.10));this.fallbackRender();},{passive:false});this.fallbackWheelBound=true;}
 }
 updateLabels(){if(!this.labels)return;OFFICE_ROOMS.forEach((d,i)=>{const p=this.project([d.position[0],d.floor*FLOOR_HEIGHT+2.55,d.position[1]-2.25]);const el=this.labels[i];if(!this.rooms.includes(d)){el.style.display='none';return;}if(!p){el.style.display='none';return;}el.style.display='';el.style.left=p.x+'px';el.style.top=p.y+'px';el.classList.toggle('active',this.selected===d.id);});}
 _animate(time=0){if(this.dead)return;this.frame=requestAnimationFrame(this._animate);if(!this.gl||!this.width||!this.height)return;if(this.contextLost||document.visibilityState==='hidden')return;if(time&&this.prevFrame&&time-this.prevFrame<(this.lowDetail?65:34))return;this.prevFrame=time;this._camera();const g=this.gl;g.clear(g.COLOR_BUFFER_BIT|g.DEPTH_BUFFER_BIT);g.useProgram(this.program);this.office(performance.now()/1000);this.updateLabels();}
 destroy(){this.dead=true;cancelAnimationFrame(this.frame);this.resizeObserver?.disconnect();this.container.innerHTML='';this.gl?.deleteProgram?.(this.program);}
}
