import {INITIAL_TASKS, AGENTS, TASK_STATES} from './config.js';
const KEY='mep-ai-company3d.v1';
const deepCopy=v=>JSON.parse(JSON.stringify(v));
const now=()=>new Date().toISOString();
function makeInitial(){return {tasks:deepCopy(INITIAL_TASKS),events:[{id:'evt-1',at:now(),kind:'system',text:'Khởi tạo không gian demo. Chưa có AI thật.'}],selectedDept:'director',createdAt:now(),simulated:false};}
export function loadState(){try{const data=JSON.parse(localStorage.getItem(KEY)||'null');if(data&&Array.isArray(data.tasks)&&Array.isArray(data.events))return data;}catch{}return makeInitial();}
export function persistState(state){localStorage.setItem(KEY,JSON.stringify(state));}
export function logEvent(state,text,kind='activity'){state.events.unshift({id:'evt-'+Date.now()+'-'+Math.round(Math.random()*1e6),at:now(),kind,text});state.events=state.events.slice(0,250);persistState(state);}
export function createTask(state,task){const seq=state.tasks.reduce((n,t)=>Math.max(n,parseInt((t.id.match(/\d+$/)||[])[0]||'0',10)),0)+1;const t={id:'TASK-'+String(seq).padStart(3,'0'),title:task.title.trim(),dept:task.dept,status:'todo',assignee:task.assignee||AGENTS.find(a=>a.dept===task.dept)?.id||'PM',priority:task.priority||'Trung bình',docCode:task.docCode||'',createdAt:now()};if(!t.title)throw Error('Tên công việc không được rỗng');state.tasks.unshift(t);logEvent(state,'Tạo '+t.id+': '+t.title);return t;}
export function changeTaskStatus(state,id,status){if(!TASK_STATES.includes(status))throw Error('Trạng thái không hợp lệ');const task=state.tasks.find(t=>t.id===id);if(!task)throw Error('Không tìm thấy công việc');task.status=status;logEvent(state,task.id+' → '+({todo:'Chờ xử lý',working:'Đang thực hiện',review:'Chờ duyệt',done:'Hoàn thành'}[status]));}
export function getAgentState(state,id){const tasks=state.tasks.filter(t=>t.assignee===id);if(tasks.some(t=>t.status==='working'))return 'working';if(tasks.some(t=>t.status==='review'))return 'review';return 'idle';}
export function metrics(state,docs=[]){return {agents:AGENTS.length,working:state.tasks.filter(t=>t.status==='working').length,review:state.tasks.filter(t=>t.status==='review').length,done:state.tasks.filter(t=>t.status==='done').length,docs:docs.length,tasks:state.tasks.length};}
export function getSnapshot(state,docs){return {format:'mep-ai-company-3d/export-v1',exportedAt:now(),state,documents:docs.map(({blob,...meta})=>meta),warning:'Metadata only. Download binary files individually. Store in browser IndexedDB.'};}
