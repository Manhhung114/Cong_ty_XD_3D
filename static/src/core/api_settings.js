/* V5.7.3 Settings — no API secrets in source, APK, or unencrypted localStorage.
 * Configured providers and model IDs are non-secret; API keys are kept in memory
 * until app restart or optionally encrypted with an operator-supplied passphrase.
 * Direct browser tests are opt-in and not production-grade agent execution.
 */
import {AGENTS} from './config.js';

export const API_SETTINGS_KEY='xd-mep-v573-api-config';
export const API_VAULT_KEY='xd-mep-v573-api-vault';
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const validProvider=p=>['none','openai','gemini'].includes(p);
const enc=new TextEncoder(),dec=new TextDecoder();
function b64(bytes){return btoa(String.fromCharCode(...bytes))}
function unb64(str){return Uint8Array.from(atob(str),c=>c.charCodeAt(0))}
export function safeConfig(raw){
 const source=(raw&&typeof raw==='object')?raw:{};
 const cfg={provider:validProvider(source.provider)?source.provider:'none',model:String(source.model||'').slice(0,100),agentOverrides:{}};
 if(source.agentOverrides&&typeof source.agentOverrides==='object')for(const a of AGENTS){
  const v=source.agentOverrides[a.id];if(!v||!validProvider(v.provider))continue;
  cfg.agentOverrides[a.id]={provider:v.provider,model:String(v.model||'').slice(0,100)};
 }
 return cfg;
}
async function derivedKey(passphrase,salt){
 if(!globalThis.crypto?.subtle)throw Error('Thiết bị không hỗ trợ mã hóa WebCrypto trong ngữ cảnh này');
 const key=await crypto.subtle.importKey('raw',enc.encode(passphrase),'PBKDF2',false,['deriveKey']);
 return crypto.subtle.deriveKey({name:'PBKDF2',salt,iterations:220000,hash:'SHA-256'},key,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
}
export async function encryptAPIKey(secret,passphrase){
 if(String(secret).length<10)throw Error('API key không hợp lệ');
 if(String(passphrase).length<10)throw Error('Mật khẩu bảo vệ phải dài ít nhất 10 ký tự');
 const salt=crypto.getRandomValues(new Uint8Array(16)),iv=crypto.getRandomValues(new Uint8Array(12));
 const key=await derivedKey(passphrase,salt);
 const ciphertext=new Uint8Array(await crypto.subtle.encrypt({name:'AES-GCM',iv},key,enc.encode(secret)));
 return {v:1,kdf:'PBKDF2-SHA256',iterations:220000,cipher:'AES-256-GCM',salt:b64(salt),iv:b64(iv),data:b64(ciphertext)};
}
export async function decryptAPIKey(record,passphrase){
 if(!record||record.v!==1||record.cipher!=='AES-256-GCM')throw Error('Định dạng khóa mã hóa không hợp lệ');
 try{const key=await derivedKey(passphrase,unb64(record.salt));return dec.decode(await crypto.subtle.decrypt({name:'AES-GCM',iv:unb64(record.iv)},key,unb64(record.data)));}
 catch{throw Error('Sai mật khẩu hoặc khóa đã bị thay đổi')}
}
export async function checkProviderKey(provider,key){
 if(!['openai','gemini'].includes(provider))throw Error('Hãy chọn nhà cung cấp AI');
 if(!String(key||'').trim())throw Error('Chưa nhập hoặc mở khóa API key');
 const endpoint=provider==='openai'?'https://api.openai.com/v1/models':'https://generativelanguage.googleapis.com/v1beta/models?pageSize=1';
 const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),12000);
 try{
  const response=await fetch(endpoint,{method:'GET',cache:'no-store',signal:controller.signal,headers:provider==='openai'?{Authorization:`Bearer ${key}`}:{'x-goog-api-key':key}});
  if(!response.ok)throw Error(`API ${response.status}. Kiểm tra khóa, quyền và giới hạn nhà cung cấp.`);
  return true;
 }catch(e){if(e.name==='AbortError')throw Error('Kiểm tra kết nối quá thời gian');throw e}
 finally{clearTimeout(timer)}
}
export class APISettings {
 constructor({getLanguage,onChange,notify}){
  this.getLanguage=getLanguage;this.onChange=onChange;this.notify=notify;
  let existing={};try{existing=JSON.parse(localStorage.getItem(API_SETTINGS_KEY)||'{}')}catch{}
  this.config=safeConfig(existing);this.keys={};this.agent=AGENTS[0]?.id||'CEO';
  this.provider=this.config.provider==='none'?'openai':this.config.provider;
  this.vault={};try{this.vault=JSON.parse(localStorage.getItem(API_VAULT_KEY)||'{}')||{}}catch{}
 }
 get en(){return this.getLanguage()==='en'}
 t(vi,en){return this.en?en:vi}
 _save(){localStorage.setItem(API_SETTINGS_KEY,JSON.stringify(this.config));this.onChange()}
 getConfiguredCount(){return Object.values(this.config.agentOverrides).filter(x=>x.provider!=='none').length}
 render(){const p=this.provider,over=this.config.agentOverrides[this.agent]||{provider:'none',model:''};const roleCard=window.__xdAuthRole==='admin'?'<div class="panel padded drive-settings-card" id="roleSettingsCard"><div class="panel-heading"><div><h2>🔐 '+this.t('Quản lý người dùng & phân quyền','Users and access permissions')+'</h2><p>'+this.t('Cấp quyền Admin / Cập nhật / Chỉ đọc, giới hạn theo dự án và thu hồi tài khoản trực tiếp tại đây.','Grant Admin / Edit / View access, restrict projects and revoke users directly here.')+'</p></div></div><div class="drive-sheet-actions"><button type="button" class="btn primary" data-drive-kind="access" data-drive-section="settings" id="openUserAccessManagement">'+this.t('👥 Mở quản lý phân quyền','Manage user access')+'</button></div><p class="footnote">'+this.t('Mọi thay đổi lưu tập trung trên Google Drive, không cần sửa Streamlit Secrets. Chỉ Admin đã xác thực được thao tác.','Permissions are stored in Google Drive. Only verified admins can make changes.')+'</p></div>':'';if(window.__xdCloud?.enabled){
 const status=window.__xdCloud.aiStatus||{};
 const configured=status.configured===true;
 const provider=configured?(status.provider==='gemini'?'Google Gemini':'OpenAI'):'Chưa kết nối';
 const model=configured?String(status.model||''):'—';
 const source=status.source==='drive_encrypted'?'Google Drive (mã hóa AES-256-GCM)':
  status.source==='streamlit_secrets'?'Streamlit Secrets (máy chủ)':'Chưa có';
 return '<section class="panel padded settings-panel">'+roleCard+
  '<section class="panel padded drive-settings-card"><div class="panel-heading"><h2>🔐 API & 18 Agent – cấu hình dùng chung toàn công ty</h2><span class="mini-label">V6.7.6 · SERVER-ONLY</span></div>'+
  '<p>Chỉ Admin được nhập hoặc thay khóa. Cấu hình lưu mã hóa trên Google Drive; nhân viên được cấp quyền chỉ sử dụng API thông qua máy chủ, không nhìn thấy hay nhập lại khóa.</p>'+
  '<div class="info-strip"><strong>Trạng thái:</strong> '+(configured?'✓ Đã cấu hình':'⚠ Chưa cấu hình')+
  ' · <strong>Nhà cung cấp:</strong> '+esc(provider)+
  ' · <strong>Model:</strong> '+esc(model)+
  ' · <strong>Nguồn:</strong> '+esc(source)+'</div>'+
  '<div class="portal-review-actions"><button type="button" class="btn primary" data-drive-kind="ai_config" data-drive-section="settings" id="openSharedAIConfig">⚙ Cài đặt / Thay API dùng chung</button><button type="button" class="btn outline" data-drive-kind="ai_check" data-drive-section="settings" id="checkSharedAIConnection">🔎 Kiểm tra kết nối API</button></div>'+
  '<p class="footnote">Đây là cấu hình của backend đang chạy thật, không phải vault localStorage. Sau khi Admin lưu một lần, tài khoản khác có thể chạy Agent ở sheet Nhân viên AI mà không cần cung cấp khóa.</p>'+
  '<p class="footnote">Chạy Agent có thể phát sinh chi phí; từng lượt phải được người sử dụng xác nhận. Agent chỉ tạo báo cáo nháp, kỹ sư kiểm chứng trước khi phê duyệt.</p></section>'+
  '<div class="panel padded drive-settings-card"><h3>Google Drive & phân quyền</h3><p>'+
  esc(window.__xdAccountEmail||'')+' · '+(window.__xdDriveConfigured?'Drive đã cấu hình trên máy chủ':'Drive chưa cấu hình')+
  '</p><p>Tài khoản, thư mục dự án và quyền truy cập được kiểm tra trên máy chủ.</p></div></section>';
}return `<section class="panel padded settings-panel">${roleCard}<div class="panel padded drive-settings-card" id="driveSettingsCard"><div class="panel-heading"><div><h3>${this.t('Google Drive · Kho hồ sơ dự án','Google Drive · Project files')}</h3><p>${this.t('Kết nối tài khoản Google để tải bản vẽ, BOQ, BIM và báo cáo vào đúng thư mục dự án.','Connect your Google account to upload drawings, BOQ, BIM and reports to the right project folder.')}</p></div></div><div class="info-strip">${this.t('Google Drive đã tích hợp trong Kho tài liệu, BOQ, BIM, Công việc, Phê duyệt và Dự án. Sử dụng các nút ngay tại màn hình tương ứng.','Google Drive is now integrated into Documents, BOQ, BIM, Tasks, Approvals, and Projects. Use the file buttons on each relevant screen.')}</div><p class="footnote">${esc(window.__xdAccountEmail||'')} · ${window.__xdDriveConfigured?this.t('Google Drive: đã cấu hình trên máy chủ','Google Drive: configured on server'):this.t('Google Drive: chưa cấu hình','Google Drive: not configured')}</p><p class="footnote">${this.t('Màn hình xác thực mở trong tab riêng để bảo vệ phiên đăng nhập Google; khóa không được lưu trong trình duyệt app 3D.','Authentication opens in a separate tab to protect your Google session; credentials are not stored in the 3D app browser.')}</p></div><div class="panel-heading"><div><h2>${this.t('Cài đặt API & AI Agent','API & AI Agent Settings')}</h2><p>${this.t('Thiết lập nhà cung cấp và model cho từng Agent khi chưa có máy chủ. Cấu hình không có nghĩa Agent đã tự thực thi.','Configure providers and models while offline. Configuration alone does not activate autonomous agents.')}</p></div><span class="mini-label">V5.7.3</span></div><div class="info-strip">${this.t('Chế độ cục bộ: API key chỉ giữ trong bộ nhớ phiên mở ứng dụng, trừ khi anh chủ động mã hóa bằng mật khẩu riêng. Khóa được sử dụng trực tiếp từ thiết bị khi bấm kiểm tra API; không nên dùng khóa sản xuất có hạn mức lớn.','Local mode: keys stay in memory unless explicitly encrypted with your own passphrase. A connection test calls the provider directly from this device. Avoid production keys with high spending limits.')}</div><div class="portal-section-grid"><form class="panel padded portal-form" id="apiProviderForm"><h3>${this.t('Kết nối nhà cung cấp','Provider connection')}</h3><label>${this.t('Nhà cung cấp','Provider')}<select id="apiProviderSelect" name="provider"><option value="openai" ${p==='openai'?'selected':''}>OpenAI</option><option value="gemini" ${p==='gemini'?'selected':''}>Google Gemini</option></select></label><label>${this.t('API key (không lưu dạng rõ)','API key (never saved in plaintext)')}<input type="password" name="apiKey" id="apiKey" autocomplete="off" placeholder="${this.t('Nhập API key để kiểm tra','Enter API key to test')}" /></label><small>${this.keys[p]?this.t('✓ Khóa đã nạp vào bộ nhớ phiên này','✓ Key loaded in current session'):this.vault[p]?this.t('Có khóa đã mã hóa trên thiết bị — cần mở khóa','Encrypted key on device — unlock required'):this.t('Chưa có khóa trên phiên này','No key in current session')}</small><div class="portal-review-actions"><button type="button" class="btn outline" id="apiUseSession">${this.t('Dùng trong phiên','Use in session')}</button><button type="button" class="btn primary" id="apiTest">${this.t('Kiểm tra kết nối API','Test API connection')}</button></div><p class="footnote">${this.t('Bài kiểm tra chỉ xác minh khóa và khả năng truy cập danh sách model; chưa gọi AI giải quyết nhiệm vụ. CORS/mạng có thể khiến thử trực tiếp thất bại.','Test checks key and model-list access only, not task execution. Browser networking or CORS can block direct tests.')}</p><hr><h3>${this.t('Lưu API key có mã hóa (tùy chọn)','Encrypted key vault (optional)')}</h3><label>${this.t('Mật khẩu bảo vệ riêng (ít nhất 10 ký tự)','Vault passphrase (at least 10 characters)')}<input type="password" name="passphrase" minlength="10" autocomplete="new-password"></label><div class="portal-review-actions"><button type="button" id="apiEncryptSave" class="btn outline">${this.t('Mã hóa & lưu','Encrypt & save')}</button><button type="button" id="apiUnlock" class="btn outline">${this.t('Mở khóa','Unlock key')}</button><button type="button" id="apiRemove" class="btn ghost">${this.t('Xóa khóa','Delete key')}</button></div><p class="footnote">${this.t('Nếu quên mật khẩu bảo vệ, không thể khôi phục API key đã mã hóa. Mọi phần mềm chạy trên thiết bị có thể có rủi ro khi khóa đang được sử dụng.','A forgotten passphrase cannot recover encrypted keys. Device-side secrets carry risk while in use.')}</p></form><form class="panel padded portal-form" id="apiAgentForm"><h3>${this.t('Chọn model cho từng Agent','Per-agent model settings')}</h3><label>${this.t('Nhân viên AI','AI agent')}<select id="apiAgentSelect" name="agent">${AGENTS.map(a=>`<option value="${esc(a.id)}" ${a.id===this.agent?'selected':''}>${esc(a.name)} (${esc(a.id)})</option>`).join('')}</select></label><label>${this.t('Nhà cung cấp của Agent','Agent provider')}<select name="provider"><option value="none" ${over.provider==='none'?'selected':''}>${this.t('Chưa cấu hình','Unconfigured')}</option><option value="openai" ${over.provider==='openai'?'selected':''}>OpenAI</option><option value="gemini" ${over.provider==='gemini'?'selected':''}>Google Gemini</option></select></label><label>${this.t('Mã model của Agent','Agent model ID')}<input type="text" name="model" value="${escape(over.model||'')}" placeholder="${this.t('Nhập đúng mã model từ nhà cung cấp','Enter exact provider model ID')}" maxlength="100" /></label><button type="submit" class="btn primary">${this.t('Lưu cấu hình Agent','Save agent settings')}</button><div class="info-strip">${this.getConfiguredCount()}/${AGENTS.length} ${this.t('Agent đã được gán model/nhà cung cấp; chưa thực thi AI thật.','agents have provider/model settings; AI execution is not enabled.')}</div><p class="footnote">${this.t('Giám đốc và Trưởng ban QLDA dùng chung cho cả MEP và Xây dựng, không nhân đôi cấu hình.','Company Director and Project Management Lead are shared by MEP and Construction, with one setting each.')}</p></form></div></section>`}
 bind(root){
  const q=s=>root.querySelector(s);
  const readKey=()=>String(q('#apiKey')?.value||'').trim();
  const pass=()=>String(q('#apiProviderForm [name="passphrase"]')?.value||'');
  const run=async fn=>{try{await fn()}catch(e){this.notify(e.message,true)}};
  q('#apiProviderSelect')?.addEventListener('change',e=>{this.provider=e.target.value;this.config.provider=this.provider;this._save()});
  q('#apiAgentSelect')?.addEventListener('change',e=>{this.agent=e.target.value;this.onChange()});
  q('#apiUseSession')?.addEventListener('click',()=>run(async()=>{const key=readKey();if(!key)throw Error('Chưa nhập API key');this.keys[this.provider]=key;q('#apiKey').value='';this.notify(this.t('Đã nạp khóa vào bộ nhớ tạm','Key loaded for this session'));this.onChange()}));
  q('#apiTest')?.addEventListener('click',()=>run(async()=>{const p=this.provider;const key=readKey()||this.keys[p];if(!key)throw Error('Chưa nhập hoặc mở khóa API key');const b=q('#apiTest');b.disabled=true;try{await checkProviderKey(p,key);this.keys[p]=key;this.notify(this.t('API đã phản hồi hợp lệ','API responded successfully'))}finally{b.disabled=false}}));
  q('#apiEncryptSave')?.addEventListener('click',()=>run(async()=>{const key=readKey()||this.keys[this.provider];if(!key)throw Error('Chưa nhập API key');const encrypted=await encryptAPIKey(key,pass());this.vault[this.provider]=encrypted;localStorage.setItem(API_VAULT_KEY,JSON.stringify(this.vault));this.keys[this.provider]=key;q('#apiKey').value='';q('#apiProviderForm [name="passphrase"]').value='';this.notify(this.t('Đã lưu khóa được mã hóa','Encrypted key saved'));this.onChange()}));
  q('#apiUnlock')?.addEventListener('click',()=>run(async()=>{const rec=this.vault[this.provider];if(!rec)throw Error('Chưa có khóa mã hóa');this.keys[this.provider]=await decryptAPIKey(rec,pass());q('#apiProviderForm [name="passphrase"]').value='';this.notify(this.t('Đã mở khóa vào bộ nhớ phiên','Key unlocked for this session'));this.onChange()}));
  q('#apiRemove')?.addEventListener('click',()=>{delete this.keys[this.provider];delete this.vault[this.provider];localStorage.setItem(API_VAULT_KEY,JSON.stringify(this.vault));this.notify(this.t('Đã xóa khóa của nhà cung cấp','Provider key removed'));this.onChange()});
  q('#apiAgentForm')?.addEventListener('submit',e=>{e.preventDefault();const data=Object.fromEntries(new FormData(e.currentTarget));this.config.agentOverrides[this.agent]={provider:validProvider(data.provider)?data.provider:'none',model:String(data.model||'').trim().slice(0,100)};this._save();this.notify(this.t('Đã lưu cấu hình Agent (chưa chạy AI)','Agent setting saved (AI not running)'))});
 }
}
