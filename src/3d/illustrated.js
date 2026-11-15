import {DEPARTMENTS,visibleDepartments} from '../core/config.js';

// V5.1: interactive, high-fidelity 3D-styled illustration. This is an image
// with accessible department hotspots; the WebGL view stays separately available.
export const OFFICE_ILLUSTRATION='./assets/office_xd_mep_isometric_v5_1.webp';
// Tọa độ đã hiệu chỉnh dựa trên vị trí bàn/phòng thể hiện trong ảnh 1248 x 832.
// Không đặt điểm vào khu họp nếu ảnh KHÔNG thể hiện phòng riêng.
export const OFFICE_POINTS={
  director:[50.5,23],
  electrical:[12.5,48.5], hvac:[21.8,48.8], plumbing:[30.5,46.8],
  fire:[14.0,65.5], bim:[23.0,64.8], qs:[31.7,64.0],
  architecture:[71.0,46.5], structure:[80.0,48.0], xd_bim:[89.7,49.0],
  xd_qs:[69.5,65.0], xd_planning:[78.5,65.0],
  xd_material:[86.0,66.5], xd_safety:[94.0,67.0]
};
// Trên ảnh hiện chưa có phòng riêng cho 2 bộ phận này.
// Không đặt ghim giả vào phòng họp / khu điều hành.
export const OFFICE_UNMAPPED=['qa','xd_site'];

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
    const unknown=visibleDepartments(this.view).filter(d=>!OFFICE_POINTS[d.id]);
    if(unknown.length){
      const missing=document.createElement('div'); missing.className='illustrated-missing';
      const label=document.createElement('span');label.textContent='Chưa có vị trí phòng riêng trong ảnh:';missing.append(label);
      for(const d of unknown){const b=document.createElement('button');b.type='button';b.textContent=d.name;b.onclick=()=>this.select(d.id);missing.append(b);}
      this.container.append(missing);this.missing=missing;
    }
    this.container.append(this.viewport);
    this.image=image;
    image.addEventListener('error',()=>{
      this.badge.textContent='Không tải được phối cảnh. Chọn “3D tương tác” để tiếp tục.';
    });
    this.refreshSelection();
    this._scrollToCurrent=false;
    requestAnimationFrame(()=>this.resetCamera());
    const tip=this.container.querySelector('.office-hint');
    if(tip)tip.textContent='● Chạm vào dấu tròn đúng vị trí bàn làm việc · Vuốt ngang để xem toàn cảnh';
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
  destroy(){this.container.classList.remove('illustrated-mode');this.viewport.remove();this.missing?.remove();}
}
