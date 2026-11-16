export const LEGAL_KINDS=['law','decree','circular','tcvn','qcvn','consolidated','other'];
const VI={law:'Luật',decree:'Nghị định',circular:'Thông tư',tcvn:'Tiêu chuẩn TCVN',qcvn:'Quy chuẩn QCVN',consolidated:'Văn bản hợp nhất',other:'Khác'};
const EN={law:'Laws',decree:'Decrees',circular:'Circulars',tcvn:'TCVN standards',qcvn:'QCVN regulations',consolidated:'Consolidated texts',other:'Other documents'};
const XD='Xây dựng – Quản lý dự án', MEPF='MEPF – Phòng cháy chữa cháy';
const escapeHTML=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export function legalKind(d){
 const n=String(d?.soHieu||'').toUpperCase().replace(/\s+/g,''),t=String(d?.loai||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 if(n.startsWith('TCVN'))return 'tcvn';if(n.startsWith('QCVN'))return 'qcvn';
 if(n.includes('VBHN')||t.includes('hop nhat'))return 'consolidated';
 if(t.includes('luat')||/\/QH\d+/.test(n))return 'law';
 if(t.includes('nghi dinh')||/\/NĐ-CP|\/ND-CP/.test(n))return 'decree';
 if(t.includes('thong tu')||/\/TT-[A-Z]/.test(n))return 'circular';
 return 'other';
}
export function legalStatistics(records=[]){
 const map=new Map();
 for(const d of records){const n=String(d?.soHieu||'').replace(/\s+/g,'').toUpperCase(),sector=String(d?.linhVuc||'').trim();if(n&&sector)map.set(sector+':'+n,d);}
 const blank=()=>Object.fromEntries(LEGAL_KINDS.map(k=>[k,0]));
 const totals=blank(),bySector={construction:blank(),mepf:blank(),other:blank()};
 for(const d of map.values()){const sector=d.linhVuc===XD?'construction':d.linhVuc===MEPF?'mepf':'other',kind=legalKind(d);totals[kind]++;bySector[sector][kind]++;}
 const sum=g=>Object.values(g).reduce((a,b)=>a+b,0);
 return {total:map.size,totals,bySector,sectors:{construction:sum(bySector.construction),mepf:sum(bySector.mepf),other:sum(bySector.other)},standards:totals.tcvn+totals.qcvn};
}
export function renderLegalSummary(rows,language='vi'){
 const en=language==='en',tr=(vi,english)=>en?english:vi,s=legalStatistics(rows);
 const cards=[['Tổng mục tra cứu','Catalog entries',s.total],['Xây dựng – QLDA','Construction – PM',s.sectors.construction],['MEPF – PCCC','MEPF – Fire safety',s.sectors.mepf],['TCVN + QCVN','TCVN + QCVN',s.standards]];
 const fields=[['construction','Xây dựng – QLDA','Construction – PM'],['mepf','MEPF – PCCC','MEPF – Fire safety']];
 const statCols=LEGAL_KINDS.map(k=>'<th>'+escapeHTML((en?EN:VI)[k])+'</th>').join('');
 const statRows=fields.map(([key,vi,english])=>'<tr><th scope="row">'+tr(vi,english)+'</th>'+LEGAL_KINDS.map(k=>'<td class="mono">'+s.bySector[key][k]+'</td>').join('')+'<td class="mono"><strong>'+s.sectors[key]+'</strong></td></tr>').join('');
 const totalRow='<tr class="legal-stat-total"><th scope="row">'+tr('Toàn thư viện','All entries')+'</th>'+LEGAL_KINDS.map(k=>'<td class="mono"><strong>'+s.totals[k]+'</strong></td>').join('')+'<td class="mono"><strong>'+s.total+'</strong></td></tr>';
 return '<div class="legal-stat-cards">'+cards.map(([vi,english,value])=>'<div class="legal-stat-card"><span>'+tr(vi,english)+'</span><strong class="mono">'+value+'</strong></div>').join('')+'</div>'+
 '<div class="legal-stats-heading"><h4>'+tr('Thống kê theo lĩnh vực và loại văn bản','Breakdown by discipline and document type')+'</h4><span>'+tr('Đếm theo lĩnh vực + số hiệu sau loại trùng','Unique sector + document numbers')+'</span></div>'+
 '<div class="doc-table-wrap legal-stats-wrap"><table class="data-table legal-stats-table"><thead><tr><th>'+tr('Lĩnh vực','Discipline')+'</th>'+statCols+'<th>'+tr('Tổng','Total')+'</th></tr></thead><tbody>'+statRows+totalRow+'</tbody></table></div>'+
 '<p class="legal-stats-foot">'+tr('Chỉ đếm các mục trong thư viện, kể cả bản cũ và bản hợp nhất; không phải số văn bản còn hiệu lực. Không tính mục mới chưa đối chiếu.','Catalog entries only, including historical and consolidated texts; not a count of laws in force. Unreviewed discoveries are excluded.')+'</p>';
}
export function renderLegalSources(sites,language='vi'){
 const en=language==='en',tr=(vi,english)=>en?english:vi;
 return '<details class="legal-source-directory"><summary>'+tr('Nguồn tra cứu chính thống','Official lookup sources')+' <span class="mono">('+sites.length+')</span></summary><div class="legal-source-grid">'+sites.map((site,i)=>'<a href="'+escapeHTML(site.url)+'" target="_blank" rel="noopener noreferrer"><span class="legal-source-index">'+(i+1)+'</span><span><strong>'+escapeHTML(en&&site.nameEn?site.nameEn:site.name)+'</strong><small>'+tr(site.type==='standard'?'Tiêu chuẩn / quy chuẩn':'Văn bản pháp luật',site.type==='standard'?'Standards / regulations':'Legislation')+' · '+escapeHTML(site.host)+'</small></span><span aria-hidden="true">↗</span></a>').join('')+'</div><p class="legal-stats-foot">'+tr('Nguồn tra cứu không phải văn bản được đếm; kiểm tra hiệu lực từng văn bản.','Source portals are not counted as documents; verify each document status.')+'</p></details>';
}
