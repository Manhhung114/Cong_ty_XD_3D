export const DEPARTMENTS = [
  {id:'director',name:'Ban giám đốc',short:'Điều hành',color:'#d1ad71',abbr:'GĐ',position:[-9.45,-3.45]},
  {id:'electrical',name:'Kỹ thuật Điện',short:'Điện',color:'#efb24f',abbr:'Đ',position:[-3.15,-3.45]},
  {id:'hvac',name:'Kỹ thuật HVAC',short:'HVAC',color:'#42b9bd',abbr:'H',position:[3.15,-3.45]},
  {id:'plumbing',name:'Cấp thoát nước',short:'CTN',color:'#5e9ff1',abbr:'N',position:[9.45,-3.45]},
  {id:'fire',name:'Kỹ thuật PCCC',short:'PCCC',color:'#e07a76',abbr:'P',position:[-9.45,3.45]},
  {id:'bim',name:'Phòng BIM / 3D',short:'BIM',color:'#9b91ea',abbr:'B',position:[-3.15,3.45]},
  {id:'qs',name:'Dự toán / BOQ',short:'BOQ',color:'#7bc69f',abbr:'Q',position:[3.15,3.45]},
  {id:'qa',name:'Kiểm soát QA/QC',short:'QA/QC',color:'#92a3b7',abbr:'K',position:[9.45,3.45]},
];
export const AGENTS = [
  {id:'CEO',name:'MEP Director',role:'Giám đốc AI',dept:'director',tag:'Điều phối'},
  {id:'PM',name:'Project Manager',role:'Quản lý dự án AI',dept:'director',tag:'Tiến độ'},
  {id:'ELE',name:'Electrical Engineer',role:'Kỹ sư Điện AI',dept:'electrical',tag:'Tính toán điện'},
  {id:'HVA',name:'HVAC Engineer',role:'Kỹ sư HVAC AI',dept:'hvac',tag:'Tải lạnh'},
  {id:'PLU',name:'Plumbing Engineer',role:'Kỹ sư CTN AI',dept:'plumbing',tag:'Lưu lượng'},
  {id:'FIR',name:'Fire Engineer',role:'Kỹ sư PCCC AI',dept:'fire',tag:'Kiểm tra PCCC'},
  {id:'BIM',name:'BIM Coordinator',role:'Điều phối BIM AI',dept:'bim',tag:'Mô hình IFC'},
  {id:'QSU',name:'Quantity Surveyor',role:'Kỹ sư QS AI',dept:'qs',tag:'BOQ'},
  {id:'QAC',name:'QA/QC Reviewer',role:'Kiểm soát chất lượng AI',dept:'qa',tag:'QA/QC'},
  {id:'DOC',name:'Document Controller',role:'Quản lý hồ sơ AI',dept:'qa',tag:'Tài liệu'},
];
export const CATEGORIES = [
  {id:'drawings',title:'Bản vẽ',icon:'▤',desc:'PDF, DWG, DXF, bản vẽ thiết kế',formats:'.pdf,.dwg,.dxf,.png,.jpg,.jpeg,.ifc'},
  {id:'boq',title:'BOQ / Dự toán',icon:'▦',desc:'Excel, CSV, bảng khối lượng',formats:'.xlsx,.xls,.csv,.pdf'},
  {id:'bim',title:'BIM / IFC',icon:'⬡',desc:'IFC, RVT và hồ sơ mô hình',formats:'.ifc,.rvt,.nwd,.pdf'},
  {id:'pccc',title:'PCCC',icon:'◇',desc:'Thẩm duyệt, nghiệm thu, checklist',formats:'.pdf,.xlsx,.docx'},
  {id:'reports',title:'Báo cáo',icon:'▧',desc:'Tiến độ, nghiệm thu, QA/QC',formats:'.pdf,.docx,.xlsx'},
  {id:'contracts',title:'Hợp đồng',icon:'▣',desc:'Hợp đồng, phụ lục và pháp lý',formats:'.pdf,.docx,.xlsx'}
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
export const ROADMAP = [
  {version:'V1.0',title:'Văn phòng 3D',state:'Có thể chạy thử',summary:'WebGL, 8 phòng, 10 nhân vật AI, xoay/zoom/chọn phòng, trạng thái mô phỏng.'},
  {version:'V2.0',title:'Điều phối công việc',state:'Demo chức năng',summary:'Tạo nhiệm vụ, đổi trạng thái, nhật ký thao tác. Chưa có LLM hoặc tính toán chuyên ngành.'},
  {version:'V3.0',title:'Hồ sơ bản vẽ / BOQ / BIM',state:'Quản lý nền tảng',summary:'Tệp tách theo nhóm, mã hồ sơ, revision, upload/download, mẫu CSV. Chưa đọc DWG/IFC hoặc tự bóc tách.'},
  {version:'V4.0',title:'Bảng điều hành',state:'Dashboard demo',summary:'Tổng hợp KPI, tiến độ, số hồ sơ và xuất dữ liệu JSON. Chưa có phân quyền/server.'}
];
