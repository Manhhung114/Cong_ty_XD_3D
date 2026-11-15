import {DEPARTMENTS,visibleDepartments} from '../core/config.js';

// V5.1: interactive, high-fidelity 3D-styled illustration. This is an image
// with accessible department hotspots; the WebGL view stays separately available.
export const OFFICE_ILLUSTRATION='./assets/office_xd_mep_isometric_v5_7.webp';
// Coordinates correspond to the V5.7 1586x992 illustration.
// 16 separate locations: 1 executive, 7 MEP, 8 construction.
export const OFFICE_POINTS={
 director:[50,19],
 electrical:[11,44], hvac:[22,43], plumbing:[31,43],
 fire:[11,63], bim:[23,62], qs:[31,62], qa:[17.5,82],
 architecture:[75,42], structure:[87,42], xd_bim:[76,54],
 xd_qs:[89,54], xd_planning:[75,64], xd_site:[88,65],
 xd_safety:[77,82], xd_material:[90,82]
};
// Mini workstations are drawn *in the illustration overlay*, not in a separate
// floating "missing department" menu. This makes every department reachable.
export const OFFICE_EXTRA_WORKSTATIONS={qa:'QA/QC MEP',xd_safety:'QA/QC & An toàn',xd_material:'Vật tư'};
export const OFFICE_UNMAPPED=[];

export class IllustratedOffice {
  constructor(container,options={}) {
    this.container=container;
    this.options=options;
    this.view=options.view||'all';
    this.selected=options.getState?.()?.selectedDept||'director';
    this.container.classList.add('illustrated-mode');
    this.viewport=document.createElement('div');
    this.viewport.className='illustrated-viewport';
    this.stage=document.createElement('div');
    this.stage.className='illustrated-stage';
    const image=document.createElement('img');
    image.className='illustrated-art';
    image.src=OFFICE_ILLUSTRATION;
    image.alt='Phối cảnh công ty ba tầng: ban giám đốc ở trên, kỹ thuật MEP ở trái, Xây dựng ở phải, phòng họp và bảng điều hành tại trung tâm.';
    image.decoding='async';
    image.draggable=false;
    this.stage.append(image);
    for(const [id,label] of Object.entries(OFFICE_EXTRA_WORKSTATIONS)){
      const pos=OFFICE_POINTS[id];
      const pod=document.createElement('div');pod.className='illustrated-workstation';
      pod.style.left=pos[0]+'%';pod.style.top=pos[1]+'%';
      pod.innerHTML='<span aria-hidden="true">▤</span><strong></strong>';
      pod.querySelector('strong').textContent=label;
      this.stage.append(pod);
    }
    const badge=document.createElement('div');
    badge.className='illustrated-current';
    badge.setAttribute('aria-live','polite');
    this.badge=badge;
    this.stage.append(badge);
    this.pins=new Map();
    for(const dept of visibleDepartments(this.view)){
      const pos=OFFICE_POINTS[dept.id];
      if(!pos)continue;
      const button=document.createElement('button');
      button.type='button';
      button.className='illustrated-pin';
      button.style.setProperty('--pin-color',dept.color);
      button.style.left=pos[0]+'%';button.style.top=pos[1]+'%';
      button.setAttribute('aria-label','Chọn phòng '+dept.name);
      button.title=dept.name;
      button.innerHTML='<span class="illustrated-pin-dot" aria-hidden="true"></span><span class="illustrated-pin-label"></span>';
      button.querySelector('.illustrated-pin-label').textContent=dept.short;
      button.onclick=()=>this.select(dept.id);
      this.pins.set(dept.id,button);
      this.stage.append(button);
    }
    this.viewport.append(this.stage);
    // All 16 departments now have a distinct clickable workplace on the art.
    this.container.append(this.viewport);
    this.image=image;
    image.addEventListener('error',()=>{
      this.badge.textContent='Không tải được phối cảnh. Chọn “3D tương tác” để tiếp tục.';
    });
    this.refreshSelection();
    this._scrollToCurrent=false;
    requestAnimationFrame(()=>this.resetCamera());
    const tip=this.container.querySelector('.office-hint');
    if(tip)tip.textContent='● Chạm từng phòng ban · Vuốt ngang để xem toàn cảnh';
  }
  refreshSelection(){
    for(const [id,button] of this.pins)button.classList.toggle('selected',this.selected===id);
    const selected=DEPARTMENTS.find(d=>d.id===this.selected);
    this.badge.textContent=selected?'Đang chọn: '+selected.name:'Chọn phòng để xem nhân viên AI và nhiệm vụ';
  }
  select(id){
    if(!visibleDepartments(this.view).some(d=>d.id===id))return;
    this.selected=id;
    this.refreshSelection();
    this.options.onSelect?.(id);
    const p=OFFICE_POINTS[id];
    if(p){const x=this.stage.clientWidth*p[0]/100-this.viewport.clientWidth/2;
      this.viewport.scrollTo({left:Math.max(0,x),behavior:'smooth'});}
  }
  resetCamera(){
    if(!this.viewport.isConnected)return;
    const x=this.view==='mep'?.28:this.view==='construction'?.76:.50;
    this.viewport.scrollLeft=Math.max(0,this.stage.clientWidth*x-this.viewport.clientWidth/2);
  }
  destroy(){this.container.classList.remove('illustrated-mode');this.viewport.remove();}
}
