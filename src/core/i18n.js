// Presentation-only English translations. Storage IDs, engineering codes,
// original legal records and user-entered files are never rewritten.
const STORAGE_KEY='xd-mep-ui-language-v54';
export const LANGUAGES = ['vi','en'];
export function getLanguage(){try{return localStorage.getItem(STORAGE_KEY)==='en'?'en':'vi';}catch{return 'vi';}}
export function setLanguage(v){const lang=v==='en'?'en':'vi';try{localStorage.setItem(STORAGE_KEY,lang);}catch{}document.documentElement.lang=lang;return lang;}
const STRINGS = {
 'CÔNG TY AI':'AI COMPANY','TRUNG TÂM ĐIỀU HÀNH 3D':'3D COMMAND CENTER','KHÔNG GIAN LÀM VIỆC':'WORKSPACE',
 'Văn phòng 3D':'3D Office','Khối Xây dựng':'Construction Division','Nhân viên AI':'AI Staff','Công việc':'Tasks','Kho tài liệu':'Document Library',
 'BOQ / Dự toán':'BOQ / Cost Estimate','BIM / Mô hình':'BIM / Model','Pháp luật & tiêu chuẩn':'Laws & Standards',
 'Nhật ký hoạt động':'Activity Log','Các phiên bản':'Versions','Tổng quan':'Overview','Văn phòng Xây dựng':'Construction Office',
 'Văn phòng MEP':'MEP Office','Trụ sở công ty Xây dựng & MEP':'Construction & MEP Headquarters',
 'Công ty Xây dựng & MEP 3D':'Construction & MEP 3D Company','Công ty kỹ thuật số 3D':'3D Engineering Company',
 'TRUNG TÂM ĐIỀU HÀNH XÂY DỰNG & MEP':'CONSTRUCTION & MEP COMMAND CENTER',
 'Điều hành các bộ phận, theo dõi hồ sơ và nhiệm vụ trong một không gian thống nhất.':'Manage divisions, documents and tasks in a unified workspace.',
 'DỰ ÁN MÔ PHỎNG 001':'DEMO PROJECT 001','Xuất dữ liệu':'Export data','Chạy mô phỏng':'Run simulation','Dừng mô phỏng':'Stop simulation',
 'DEMO · CHƯA CÓ AI THẬT':'DEMO · AI NOT CONNECTED','Chưa kết nối máy chủ. Dữ liệu được lưu trong trình duyệt này.':'No server connected. Data is stored in this browser.',
 'Mô phỏng':'Demo','ĐANG XỬ LÝ':'IN PROGRESS','HỒ SƠ ĐÃ LƯU':'SAVED DOCUMENTS','CHỜ PHÊ DUYỆT':'AWAITING APPROVAL',
 'NHÂN VIÊN AI':'AI STAFF','nhiệm vụ':'tasks','Trên trình duyệt':'In browser','Cần người kiểm tra':'Human review required',
 'V5.3 · VĂN PHÒNG SỐ ĐA NGÀNH':'V5.4 · MULTIDISCIPLINARY DIGITAL OFFICE','MEP + Xây dựng':'MEP + Construction',
 'Hai khối chuyên môn, hồ sơ và nhân viên AI riêng · cùng một ban điều hành.':'Two independent divisions for documents and AI staff, under one management team.',
 'Toàn công ty':'Whole company','Cơ điện MEP':'MEP Engineering','Xây dựng':'Construction','Ban điều hành':'Management',
 'Tầng MEP':'MEP Floor','Tầng Xây dựng':'Construction Floor','MÔ PHỎNG 3D':'3D DEMO','Phối cảnh chi tiết':'Detailed illustration',
 '3D tương tác':'Interactive 3D','Ảnh phối cảnh có điểm chọn phòng':'Rendered office with clickable room markers',
 'WebGL · xoay và phóng to':'WebGL · rotate and zoom','Góc nhìn':'Camera view','Phối cảnh':'Isometric','Mặt trước':'Front view',
 'Từ trên':'Top view','Tầng XD':'Construction floor','Chất lượng cao':'High quality','Tiết kiệm pin':'Battery saver','HD / Tiết kiệm':'HD / Eco',
 'Chạm vào dấu tròn để chọn phòng':'Tap a marker to select a room','Kéo xoay · Cuộn để zoom · Chọn phòng / nhân viên':'Drag to rotate · Scroll to zoom · Select room or staff',
 'Đặt lại camera':'Reset camera','Trạng thái AI đang mô phỏng':'AI state is simulated','CHẠM VÀO PHÒNG ĐỂ XEM NHIỆM VỤ':'TAP A ROOM TO SEE TASKS',
 'Công việc trong khối':'Division tasks','Tất cả công việc':'All tasks','Phòng ban':'Departments','Chọn để xem vị trí trên 3D':'Select to locate in 3D',
 'PHÒNG ĐANG CHỌN':'SELECTED DEPARTMENT','NHÂN SỰ TRONG PHÒNG':'ROOM STAFF','NHIỆM VỤ LIÊN QUAN':'RELATED TASKS',
 'Đang làm':'Working','Chờ duyệt':'Pending approval','Sẵn sàng':'Available','Chưa có nhiệm vụ trong phòng này.':'No tasks assigned to this department.',
 'Giao nhiệm vụ':'Assign task','Bảng công việc xây dựng & MEP':'Construction & MEP task board','Tạo nhiệm vụ':'Create task',
 'Chờ xử lý':'To do','Đang thực hiện':'In progress','Hoàn thành':'Done','Chuyển trạng thái':'Change status',
 'Chưa có nhiệm vụ':'No tasks','Mã hồ sơ':'Document code','Mức ưu tiên':'Priority','Cao':'High','Trung bình':'Medium','Thấp':'Low',
 'Nhân viên AI – MEP & Xây dựng':'AI Staff – MEP & Construction',
 'Chọn khối để lọc nhân sự. Chưa kết nối hệ thống AI thực tế.':'Filter staff by division. Live AI is not connected.',
 'Kho tài liệu hai khối độc lập':'Independent division libraries','Tải tài liệu lên':'Upload document',
 'Danh mục hồ sơ':'Document register','Mã hồ sơ và lịch sử sửa đổi được quản lý độc lập giữa MEP và Xây dựng.':'Revision histories are separate for MEP and Construction.',
 'KHỐI':'DIVISION','MÃ HỒ SƠ':'DOCUMENT ID','LOẠI':'TYPE','TÊN TỆP':'FILE NAME','CẬP NHẬT':'UPDATED',
 'Lịch sử':'History','Chưa có hồ sơ. Có thể cập nhật sau, không cần kết nối Drive ngay.':'No documents yet. You can upload files later.',
 'BOQ / Dự toán theo khối':'Division BOQ / Cost Estimate','Đọc CSV':'Import CSV','Tổng thành tiền tạm tính':'Estimated total',
 'SỐ DÒNG BOQ':'BOQ ROWS','TỔNG THÀNH TIỀN TẠM TÍNH':'ESTIMATED TOTAL','Dữ liệu minh họa':'Demo data',
 'Chưa bao gồm thuế và điều chỉnh':'Tax and adjustments excluded','MÔ TẢ CÔNG VIỆC':'WORK DESCRIPTION','KHỐI LƯỢNG':'QUANTITY',
 'ĐƠN GIÁ':'UNIT PRICE','THÀNH TIỀN':'AMOUNT','Mẫu BOQ':'BOQ template','BOQ Xây dựng':'Construction BOQ',
 'Văn bản pháp luật và tiêu chuẩn kỹ thuật':'Laws, regulations and technical standards',
 'THƯ VIỆN PHÁP LÝ · CẬP NHẬT 15/11/2026':'LEGAL LIBRARY · REVIEWED NOV 15, 2026',
 'Tách riêng MEPF–PCCC và Xây dựng–Quản lý dự án; mỗi văn bản có đường dẫn nguồn chính thống để kiểm tra.':'Separate MEPF & Fire Safety from Construction & Project Management; each record links to an official source.',
 'Tải bảng Excel':'Download Excel register','Lĩnh vực':'Discipline','Loại văn bản':'Document type','Tất cả lĩnh vực':'All disciplines',
 'Tất cả loại văn bản':'All document types','Tìm theo số hiệu hoặc tên':'Search by code or title',
 'Ví dụ: 135/2025, báo cháy, HVAC…':'Example: 135/2025, fire alarm, HVAC…','Hiển thị':'Showing',
 'văn bản được đối chiếu nguồn chính thống':'records with official source links','LĨNH VỰC':'DISCIPLINE','NHÓM':'GROUP',
 'SỐ HIỆU':'NUMBER','TÊN VĂN BẢN / TIÊU CHUẨN':'LAW / STANDARD TITLE','TÌNH TRẠNG':'STATUS',
 'NGUỒN CHÍNH THỐNG':'OFFICIAL SOURCE','Không có kết quả phù hợp':'No matching records',
 'Xây dựng – Quản lý dự án':'Construction – Project Management','MEPF – Phòng cháy chữa cháy':'MEPF – Fire Safety',
 'Tiêu chuẩn TCVN':'National standard (TCVN)','Tiêu chuẩn đã thay thế':'Superseded standard',
 'Còn hiệu lực (VSQI)':'Active (VSQI)','Hết hiệu lực (VSQI)':'Withdrawn (VSQI)',
 'Chờ đối chiếu nguồn':'Awaiting source review','Cổng TCVN/VSQI':'VSQI standards portal',
 'Kiến trúc':'Architecture','Kết cấu':'Structures','Nền móng':'Foundations','Nền móng – lịch sử':'Foundations – History',
 'Cấp thoát nước':'Water & Drainage','Điện':'Electrical','PCCC':'Fire Safety',
 'Kỹ thuật Điện':'Electrical Engineering','Kỹ thuật HVAC':'HVAC Engineering','Kỹ thuật PCCC':'Fire Engineering','BIM cơ điện':'MEP BIM',
 'Dự toán MEP':'MEP Quantity Surveying','QA/QC MEP':'MEP QA/QC','BIM xây dựng':'Construction BIM',
 'QS xây dựng':'Construction QS','Kế hoạch thi công':'Construction Planning','Quản lý hiện trường':'Site Management',
 'QA/QC & An toàn XD':'Construction QA/QC & Safety','Quản lý vật tư':'Materials Management',
 'Ban giám đốc':'Board of Directors','NHIỆM VỤ':'TASK','TÊN CÔNG VIỆC':'TASK NAME','PHÒNG BAN':'DEPARTMENT',
 'MỨC ƯU TIÊN':'PRIORITY','LOẠI HỒ SƠ':'DOCUMENT CATEGORY','TỆP ĐÍNH KÈM':'ATTACHMENT','GHI CHÚ CẬP NHẬT':'REVISION NOTES',
 'Hủy':'Cancel','Lưu bản mới':'Save new version','Tải bản sửa đổi mới':'Upload new revision',
 'Xóa bản này':'Delete this revision','Tải gốc':'Download original','QUẢN LÝ LẦN SỬA ĐỔI':'REVISION HISTORY',
 'Không có mô tả thay đổi':'No change description','Tạo công việc MEP / Xây dựng':'Create MEP / Construction task',
 'Tải hồ sơ MEP / Xây dựng':'Upload MEP / Construction document',
 'KHỐI CHUYÊN MÔN':'DIVISION','Tiến độ XD':'Construction Schedule','Vật tư XD':'Construction Materials','An toàn XD':'Construction Safety',
 'Bản vẽ':'Drawings','Báo cáo':'Reports','Hợp đồng':'Contracts','Lưu hồ sơ':'Save documents',
 'Chưa có mô hình BIM đang mở':'No BIM model is open','Kiến trúc BIM':'BIM architecture',
 'LỘ TRÌNH TÍCH HỢP':'INTEGRATION ROADMAP','HỒ SƠ BIM HIỆN CÓ':'BIM DOCUMENTS',
 'Phiên bản và trạng thái nghiệm thu':'Versions & Acceptance Status','Xem ghi chú cập nhật':'View release notes',
 'TRẠNG THÁI':'STATUS','Hoạt động':'Activity','Chưa có nhật ký hoạt động.':'No activity logs yet.',
 'Cập nhật từ GitHub':'Update from GitHub','Nhập JSON':'Import JSON','Tải mẫu JSON':'Download JSON template',
 'Đặt lại danh mục':'Reset catalog','DANH MỤC TCVN MỞ RỘNG':'EXPANDED TCVN REGISTER',
 'Đã đối chiếu VSQI':'Reviewed against VSQI','nguồn':'source','nguồn chính thống':'official source',
 'Số lượng TCVN':'TCVN records','Ngày rà soát':'Review date','Chưa kiểm định trên thiết bị thật':'Not yet verified on a real device',
};

Object.assign(STRINGS,{
  'KHÔNG GIAN':'WORKSPACE','THƯ VIỆN PHÁP LÝ':'LEGAL LIBRARY',
  'Danh mục pháp luật, quy chuẩn và tiêu chuẩn có nguồn chính thống cho hai lĩnh vực.':'A register of laws, regulations and standards with official sources for both divisions.',
  'Danh mục pháp luật, quy chuẩn và tiêu chuẩn có official source cho hai lĩnh vực.':'A register of laws, regulations and standards with official sources for both divisions.',
  'Lưu ý: Danh mục phục vụ tra cứu, không phải kết luận áp dụng pháp luật cho từng dự án. Cần kiểm tra hiệu lực, văn bản sửa đổi, điều khoản chuyển tiếp; TCVN không mặc nhiên bắt buộc nếu không được viện dẫn. Các văn bản hợp nhất dùng tham khảo, không phải quy phạm độc lập. Không sao chép bản thương mại của tiêu chuẩn.':'Notice: This register is for reference only, not a legal determination for a project. Verify effective status, amendments, transitional clauses and applicability; TCVN standards are not automatically mandatory unless incorporated by reference. Consolidated texts are reference material, not separate regulations. Do not reproduce copyrighted standards.',
  'Lưu ý: Danh mục phục vụ tra cứu, không phải kết luận áp dụng pháp luật cho từng dự án. Cần kiểm tra hiệu lực, văn bản sửa đổi, điều khoản chuyển tiếp; TCVN không mặc nhiên bắt buộc nếu không được viện dẫn. Các văn bản hợp nhất dùng tham khảo, không phải quy phạm độc lập. Không sao chép bản thương mại của tiêu chuẩn.':'Notice: This register is for reference only, not a legal determination for a project. Verify effective status, amendments, transitional clauses and applicability; TCVN standards are not automatically mandatory unless incorporated by reference. Consolidated texts are reference material, not separate regulations. Do not reproduce copyrighted standards.',
  'Luật và QLDA':'Law & Project Management','Quản lý hoạt động XD':'Construction Activity Management',
  'Hiện hành':'In force','Hiện hành – có hợp nhất':'In force – consolidated','Hết hiệu lực':'Withdrawn',
  'Cổng văn bản Chính phủ':'Government Legal Document Portal','Cổng văn bản Chính phủ ↗':'Government legal portal ↗',
  'Cổng thông tin TCVN / VSQI':'VSQI National Standards Portal','Bộ Xây dựng':'Ministry of Construction',
  'Quốc hội':'National Assembly','Pháp luật':'Law',
  'Công ty AI Xây dựng & MEP':'Construction & MEP AI Company',
  'Đã cập nhật trạng thái công việc':'Task status updated',
  'Đã khôi phục danh mục gốc':'Built-in catalog restored',
  'Đã cập nhật':'Updated','mục':'entries','dòng':'rows','tệp':'files','đã lưu':'saved',
  'Tất cả':'All','Điều hành':'Management','Hiện trường':'Site','Vật tư':'Materials',
  'Văn bản pháp luật':'Legal documents','Quy chuẩn':'Technical regulations',
  'Chỉ tra cứu lịch sử':'Historical reference only',
  'Chưa đồng bộ GitHub/Drive và chưa có bảo mật phía máy chủ.':'Not synchronized to GitHub/Drive. Server-side security is not configured.',
  'Lưu trữ trong IndexedDB của trình duyệt hiện tại.':'Stored in this browser’s IndexedDB.',
  'Ngày rà soát:':'Reviewed:','CHƯA CÓ AI THẬT':'NO LIVE AI',
  'LỰA CHỌN NGÔN NGỮ':'LANGUAGE','Ngôn ngữ / Language':'Language',
  'Xem phòng đang chọn':'View selected room','Không có hồ sơ':'No records',
  'Chưa có AI thật':'AI is not connected'
});
const rules=Object.entries(STRINGS).sort((a,b)=>b[0].length-a[0].length);
export function translateText(original,lang=getLanguage()){
  if(lang!=='en')return String(original??'');
  // Replace longest known phrases first, preserving technical acronyms and codes.
  let out=String(original??'');const replacements=[];
  for(let i=0;i<rules.length;i++){
    const [source,dest]=rules[i];if(!out.includes(source))continue;
    const marker=`\u0001${i}\u0002`;out=out.split(source).join(marker);replacements.push([marker,dest]);
  }
  for(const [marker,dest] of replacements)out=out.split(marker).join(dest);
  return out;
}
export function translateDom(root=document.body,lang=getLanguage()){
  if(lang!=='en'||!root)return;
  const doc=root.ownerDocument||document;
  const walker=doc.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(n){
    if(!n.parentElement||/^(SCRIPT|STYLE|TEXTAREA|CODE)$/.test(n.parentElement.tagName))return NodeFilter.FILTER_REJECT;
    return n.nodeValue.trim()?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT;
  }});
  let n;while(n=walker.nextNode())n.nodeValue=translateText(n.nodeValue,lang);
  for(const el of root.querySelectorAll('[title],[placeholder],[aria-label],[alt]')){
    for(const key of ['title','placeholder','aria-label','alt'])if(el.hasAttribute(key))el.setAttribute(key,translateText(el.getAttribute(key),lang));
  }
}
