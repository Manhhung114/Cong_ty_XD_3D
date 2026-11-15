export const DIVISIONS = [
  {id:'all',name:'Toàn công ty',short:'Tất cả'},
  {id:'mep',name:'Cơ điện MEP',short:'MEP'},
  {id:'construction',name:'Xây dựng',short:'XD'}
];
export const DEPARTMENTS = [
  {id:'director',name:'Ban giám đốc',short:'Điều hành',division:'shared',color:'#f0be72',abbr:'GĐ',position:[-9.45,-3.45],floor:0},
  {id:'electrical',name:'Kỹ thuật Điện',short:'Điện',division:'mep',color:'#efb24f',abbr:'Đ',position:[-3.15,-3.45],floor:0},
  {id:'hvac',name:'Kỹ thuật HVAC',short:'HVAC',division:'mep',color:'#42b9bd',abbr:'H',position:[3.15,-3.45],floor:0},
  {id:'plumbing',name:'Cấp thoát nước',short:'CTN',division:'mep',color:'#5e9ff1',abbr:'N',position:[9.45,-3.45],floor:0},
  {id:'fire',name:'Kỹ thuật PCCC',short:'PCCC',division:'mep',color:'#e07a76',abbr:'P',position:[-9.45,3.45],floor:0},
  {id:'bim',name:'BIM cơ điện',short:'BIM-MEP',division:'mep',color:'#9b91ea',abbr:'B',position:[-3.15,3.45],floor:0},
  {id:'qs',name:'Dự toán MEP',short:'BOQ-MEP',division:'mep',color:'#7bc69f',abbr:'Q',position:[3.15,3.45],floor:0},
  {id:'qa',name:'QA/QC MEP',short:'QA-MEP',division:'mep',color:'#92a3b7',abbr:'K',position:[9.45,3.45],floor:0},
  {id:'architecture',name:'Kiến trúc',short:'Kiến trúc',division:'construction',color:'#ed9a83',abbr:'KT',position:[-9.45,-3.45],floor:1},
  {id:'structure',name:'Kết cấu',short:'Kết cấu',division:'construction',color:'#e5b878',abbr:'KC',position:[-3.15,-3.45],floor:1},
  {id:'xd_bim',name:'BIM xây dựng',short:'BIM-XD',division:'construction',color:'#9b8fea',abbr:'BX',position:[3.15,-3.45],floor:1},
  {id:'xd_qs',name:'QS xây dựng',short:'BOQ-XD',division:'construction',color:'#6dcab7',abbr:'QX',position:[9.45,-3.45],floor:1},
  {id:'xd_planning',name:'Kế hoạch thi công',short:'Tiến độ',division:'construction',color:'#7aa9e4',abbr:'KH',position:[-9.45,3.45],floor:1},
  {id:'xd_site',name:'Quản lý hiện trường',short:'Hiện trường',division:'construction',color:'#eeac61',abbr:'HT',position:[-3.15,3.45],floor:1},
  {id:'xd_safety',name:'QA/QC & An toàn XD',short:'AT/CL',division:'construction',color:'#dc8faa',abbr:'AT',position:[3.15,3.45],floor:1},
  {id:'xd_material',name:'Quản lý vật tư',short:'Vật tư',division:'construction',color:'#91c181',abbr:'VT',position:[9.45,3.45],floor:1}
];
export const FLOOR_HEIGHT=4.35;
export const departmentDivision=dept=>dept?.division==='shared'?'shared':dept?.division||'mep';
export const visibleDepartments=view=>DEPARTMENTS.filter(d=>view==='all'||d.division===view||(view==='mep'&&d.division==='shared'));
export const AGENTS = [
  {id:'CEO',name:'Company Director',role:'Giám đốc công ty AI',dept:'director',tag:'Điều phối liên ngành'},
  {id:'PM',name:'Project Manager',role:'Quản lý dự án AI',dept:'director',tag:'Tiến độ tổng thể'},
  {id:'ELE',name:'Electrical Engineer',role:'Kỹ sư Điện AI',dept:'electrical',tag:'Tính toán điện'},
  {id:'HVA',name:'HVAC Engineer',role:'Kỹ sư HVAC AI',dept:'hvac',tag:'Tải lạnh'},
  {id:'PLU',name:'Plumbing Engineer',role:'Kỹ sư CTN AI',dept:'plumbing',tag:'Lưu lượng'},
  {id:'FIR',name:'Fire Engineer',role:'Kỹ sư PCCC AI',dept:'fire',tag:'Kiểm tra PCCC'},
  {id:'BIM',name:'MEP BIM Coordinator',role:'Điều phối BIM MEP AI',dept:'bim',tag:'Mô hình cơ điện'},
  {id:'QSU',name:'MEP Quantity Surveyor',role:'Kỹ sư QS MEP AI',dept:'qs',tag:'BOQ cơ điện'},
  {id:'QAC',name:'MEP QA/QC Reviewer',role:'Kiểm soát MEP AI',dept:'qa',tag:'QA/QC'},
  {id:'DOC',name:'Document Controller',role:'Quản lý hồ sơ AI',dept:'qa',tag:'Tài liệu'},
  {id:'ARC',name:'Architectural Engineer',role:'Kỹ sư Kiến trúc AI',dept:'architecture',tag:'Bản vẽ kiến trúc'},
  {id:'STR',name:'Structural Engineer',role:'Kỹ sư Kết cấu AI',dept:'structure',tag:'Cột, dầm, sàn'},
  {id:'XBI',name:'Construction BIM',role:'BIM xây dựng AI',dept:'xd_bim',tag:'Mô hình kiến trúc/kết cấu'},
  {id:'XQS',name:'Construction Quantity Surveyor',role:'Kỹ sư QS xây dựng AI',dept:'xd_qs',tag:'BOQ xây dựng'},
  {id:'PLN',name:'Construction Planner',role:'Kỹ sư Kế hoạch AI',dept:'xd_planning',tag:'Tiến độ thi công'},
  {id:'SIT',name:'Site Engineer',role:'Kỹ sư Hiện trường AI',dept:'xd_site',tag:'Theo dõi thi công'},
  {id:'HSE',name:'Construction QA/HSE',role:'An toàn & QA/QC XD AI',dept:'xd_safety',tag:'Chất lượng/An toàn'},
  {id:'MAT',name:'Material Controller',role:'Kỹ sư Vật tư AI',dept:'xd_material',tag:'Vật liệu xây dựng'}
];
export const CATEGORIES = [
  {id:'drawings',title:'Bản vẽ',icon:'▤',desc:'PDF, DWG, DXF, bản vẽ thiết kế',formats:'.pdf,.dwg,.dxf,.png,.jpg,.jpeg,.ifc'},
  {id:'boq',title:'BOQ / Dự toán',icon:'▦',desc:'Excel, CSV, bảng khối lượng',formats:'.xlsx,.xls,.csv,.pdf'},
  {id:'bim',title:'BIM / IFC',icon:'⬡',desc:'IFC, RVT và hồ sơ mô hình',formats:'.ifc,.rvt,.nwd,.pdf'},
  {id:'pccc',title:'PCCC',icon:'◇',desc:'Thẩm duyệt, nghiệm thu, checklist',formats:'.pdf,.xlsx,.docx'},
  {id:'reports',title:'Báo cáo',icon:'▧',desc:'Tiến độ, nghiệm thu, QA/QC',formats:'.pdf,.docx,.xlsx'},
  {id:'contracts',title:'Hợp đồng',icon:'▣',desc:'Hợp đồng, phụ lục và pháp lý',formats:'.pdf,.docx,.xlsx'},
  {id:'architecture',title:'Kiến trúc',icon:'⌂',desc:'Hồ sơ kiến trúc, chi tiết, hoàn thiện',formats:'.pdf,.dwg,.dxf'},
  {id:'structure',title:'Kết cấu',icon:'▥',desc:'Móng, cột, dầm, sàn, thuyết minh tính toán',formats:'.pdf,.dwg,.xlsx'},
  {id:'schedule',title:'Tiến độ XD',icon:'◷',desc:'Kế hoạch, Gantt, tiến độ hiện trường',formats:'.pdf,.xlsx,.csv'},
  {id:'materials',title:'Vật tư XD',icon:'▣',desc:'Vật liệu, nhập xuất, submittal và mẫu',formats:'.pdf,.xlsx,.csv'},
  {id:'safety',title:'An toàn XD',icon:'◇',desc:'QA/QC, HSE, checklist hiện trường',formats:'.pdf,.xlsx,.docx'}
];
export const TASK_STATES = ['todo','working','review','done'];
export const TASK_STATE_LABELS = {todo:'Chờ xử lý',working:'Đang thực hiện',review:'Chờ duyệt',done:'Hoàn thành'};
export const INITIAL_TASKS = [
  {id:'TASK-001',title:'Rà soát sơ đồ cấp điện tầng điển hình',dept:'electrical',status:'working',assignee:'ELE',priority:'Cao',docCode:'DRW-E-001'},
  {id:'TASK-002',title:'Kiểm tra tải lạnh khu vực văn phòng',dept:'hvac',status:'todo',assignee:'HVA',priority:'Trung bình',docCode:''},
  {id:'TASK-003',title:'Đối chiếu khối lượng thiết bị điện',dept:'qs',status:'review',assignee:'QSU',priority:'Cao',docCode:'BOQ-MEP-001'},
  {id:'TASK-004',title:'Kiểm tra checklist nghiệm thu PCCC',dept:'fire',status:'todo',assignee:'FIR',priority:'Cao',docCode:''},
  {id:'TASK-005',title:'Tổng hợp các xung đột BIM',dept:'bim',status:'working',assignee:'BIM',priority:'Trung bình',docCode:''},
  {id:'TASK-006',title:'Kiểm tra biên bản QA/QC trước phê duyệt',dept:'qa',status:'todo',assignee:'QAC',priority:'Trung bình',docCode:''}
];
export const CONSTRUCTION_SAMPLE_TASKS = [
  {id:'TASK-007',title:'Rà soát mặt bằng kiến trúc tầng điển hình',dept:'architecture',status:'working',assignee:'ARC',priority:'Cao',docCode:'XD-ARC-001'},
  {id:'TASK-008',title:'Đối chiếu kết cấu dầm, cột và sàn',dept:'structure',status:'todo',assignee:'STR',priority:'Cao',docCode:'XD-STR-001'},
  {id:'TASK-009',title:'Tổng hợp BOQ xây dựng phần thô',dept:'xd_qs',status:'review',assignee:'XQS',priority:'Trung bình',docCode:'XD-BOQ-001'},
  {id:'TASK-010',title:'Cập nhật tiến độ thi công tuần',dept:'xd_planning',status:'todo',assignee:'PLN',priority:'Cao',docCode:'XD-PLN-001'},
  {id:'TASK-011',title:'Rà soát biện pháp an toàn và chất lượng thi công',dept:'xd_safety',status:'working',assignee:'HSE',priority:'Cao',docCode:'XD-HSE-001'},
  {id:'TASK-012',title:'Đối chiếu vật tư xây dựng đã trình duyệt',dept:'xd_material',status:'todo',assignee:'MAT',priority:'Trung bình',docCode:'XD-MAT-001'}
];
export const ROADMAP = [
  {version:'V1.0',title:'Văn phòng 3D',state:'Có thể chạy thử',summary:'WebGL, mô hình phòng ban, nhân viên 3D, xoay/zoom/chọn phòng, trạng thái mô phỏng.'},
  {version:'V2.0',title:'Điều phối công việc',state:'Demo chức năng',summary:'Tạo nhiệm vụ, đổi trạng thái, nhật ký thao tác. Chưa có LLM hoặc tính toán chuyên ngành.'},
  {version:'V3.0',title:'Hồ sơ bản vẽ / BOQ / BIM',state:'Quản lý nền tảng',summary:'Phân loại tệp, mã hồ sơ, revision, upload/download, mẫu CSV. Chưa tự bóc tách.'},
  {version:'V4.0',title:'Bảng điều hành',state:'Dashboard demo',summary:'Tổng hợp KPI, tiến độ, hồ sơ và xuất dữ liệu JSON. Chưa có phân quyền/server.'},
  {version:'V5.0',title:'Nhánh Xây dựng',state:'Đã tích hợp demo',summary:'2 tầng MEP + Xây dựng, 16 phòng, 18 Agent, công việc và tệp riêng theo nhánh; chưa AI thật.'},
  {version:'V5.1',title:'Phối cảnh văn phòng chi tiết',state:'Có thể chạy thử',summary:'Ảnh phối cảnh isometric 3D có 16 điểm chọn phòng; chuyển qua WebGL tương tác khi cần; chưa phải 3D photoreal-time.'}
];
