/* High-contrast command bar. All alerts are derived from authenticated server data. */
const OFFICE_IMAGE='./assets/office_xd_mep_isometric_v5_7.webp';
const safe=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const el=id=>document.getElementById(id);
const ROLE_LABELS={admin:'Admin',update:'Nhân viên',read:'Chỉ đọc',member:'Nhân viên'};
function showPanel(heading,body){
 const host=el('modalRoot');
 if(!host)return;
 host.innerHTML='<div class="modal-backdrop command-backdrop" id="commandBackdrop">'+
 '<div class="modal command-modal" role="dialog" aria-modal="true" aria-labelledby="commandPanelTitle">'+
 '<button type="button" class="command-modal-close" id="commandClose" aria-label="Đóng">×</button>'+
 '<h2 id="commandPanelTitle">'+safe(heading)+'</h2>'+body+'</div></div>';
 el('commandClose')?.addEventListener('click',()=>{host.textContent='';});
 el('commandBackdrop')?.addEventListener('mousedown',e=>{
  if(e.target.id==='commandBackdrop')host.textContent='';
 });
 el('commandClose')?.focus();
}
export function updateCommandShell(tab,subtitle=''){
 const role=window.__xdAuthRole||'member';
 const cloud=window.__xdCloud||{};
 const alerts=cloud.companyMetrics?.alerts||[];
 const monitor=tab==='monitor';
 for(const image of document.querySelectorAll('[data-brand-image]')){
  if(!image.getAttribute('src'))image.setAttribute('src',OFFICE_IMAGE);
 }
 const title=el('commandTitle');
 if(title)title.textContent=monitor?
  'Giám sát Agent — Hoạt động & Phối hợp theo thời gian thực':
  (subtitle||'Công ty Xây dựng & MEP AI 3D');
 const live=el('commandLive');
 if(live){
  live.classList.toggle('is-connected',Boolean(cloud.enabled));
  const text=live.querySelector('span');
  if(text)text.textContent=cloud.enabled?
   (monitor?'Gần thời gian thực · 15 giây':'Google Drive đã xác thực'):
   'Chưa kết nối dữ liệu';
 }
 const roleLabel=el('commandRole');
 if(roleLabel)roleLabel.textContent=ROLE_LABELS[role]||'Nhân viên';
 const avatar=el('commandAvatar');
 if(avatar)avatar.textContent=role==='admin'?'AD':role==='update'?'NV':'X';
 const count=el('commandAlertCount');
 if(count){count.textContent=String(alerts.length);count.hidden=alerts.length===0;}
 el('commandNotifications')?.setAttribute('aria-label','Xem '+alerts.length+' cảnh báo công việc');
 el('commandNotifications').onclick=()=>{
  showPanel('Thông báo & Cảnh báo',
   alerts.length?'<ul class="command-message-list">'+alerts.slice(0,12).map(x=>
    '<li><strong>'+safe(x.title)+'</strong><p>'+safe(x.action)+'</p></li>').join('')+'</ul>':
    '<p>Chưa có cảnh báo thuộc các dự án được cấp quyền.</p>'+
    '<p class="command-message-note">Không có thông báo giả. Thông báo sẽ xuất hiện khi dữ liệu thật có cảnh báo.</p>');
 };
 el('commandHelp').onclick=()=>showPanel('Hướng dẫn sử dụng',
  '<p>Mở <b>Giám sát Agent</b> để xem các hoạt động của MEP, XD và phối hợp chéo. Chọn dự án, khoảng thời gian và phòng ban ở phía trên biểu đồ.</p>'+
  '<p>Màn hình làm mới theo chu kỳ 15 giây khi được mở. Lượt Agent chỉ được ghi nhận sau khi hoàn thành, không phải trạng thái RUNNING của worker.</p>'+
  '<p>Để xem, tải hoặc thẩm tra hồ sơ, sử dụng các sheet chuyên trách và quyền đã được Admin cấp.</p>');
 el('commandAccount').onclick=()=>showPanel('Tài khoản & quyền truy cập',
  '<p><b>Vai trò:</b> '+safe(ROLE_LABELS[role]||'Nhân viên')+'</p>'+
  (window.__xdAccountEmail?'<p><b>Google:</b> '+safe(window.__xdAccountEmail)+'</p>':'')+
  '<p class="command-message-note">Đăng xuất bằng nút Đăng xuất của Streamlit phía ngoài ứng dụng. Chỉ Admin có quyền mở mục Cài đặt hệ thống.</p>');
}
