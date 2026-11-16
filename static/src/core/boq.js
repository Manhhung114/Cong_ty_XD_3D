export function parseDelimited(text,separator=','){
  const source=String(text||'').replace(/^\uFEFF/,'');
  const rows=[];let current=[],field='',quoted=false;
  for(let i=0;i<source.length;i++){
    const c=source[i];
    if(c==='"'){if(quoted && source[i+1]==='"'){field+='"';i++;}else quoted=!quoted;}
    else if(c===separator && !quoted){current.push(field.trim());field='';}
    else if((c==='\n'||c==='\r') && !quoted){if(c==='\r' && source[i+1]==='\n')i++;current.push(field.trim());if(current.some(x=>x!==''))rows.push(current);current=[];field='';}
    else field+=c;
  }
  if(quoted)throw Error('CSV có dấu nháy kép chưa đóng');
  current.push(field.trim());if(current.some(x=>x!==''))rows.push(current);
  return rows;
}
export function numberVN(value){let s=String(value??'0').trim().replace(/\s/g,'');if(!s)return 0;if(s.includes(',')&&s.includes('.')){if(s.lastIndexOf(',')>s.lastIndexOf('.'))s=s.replace(/\./g,'').replace(',','.');else s=s.replace(/,/g,'');}else if(s.includes(',')){if(/^[-+]?\d{1,3}(,\d{3})+$/.test(s))s=s.replace(/,/g,'');else s=s.replace(',','.');}else if(/^[-+]?\d{1,3}(\.\d{3})+$/.test(s))s=s.replace(/\./g,'');const n=Number(s);if(!Number.isFinite(n))throw Error('Giá trị số không hợp lệ: '+value);return n;}
export function parseBOQCSV(text){const source=String(text||'');const header=source.split(/\r?\n/,1)[0];const separator=(header.match(/;/g)||[]).length>(header.match(/,/g)||[]).length?';':',';const rows=parseDelimited(source,separator);if(!rows.length)return [];const keys=rows.shift().map(s=>s.toLowerCase().trim());const col=(...variants)=>keys.findIndex(k=>variants.includes(k));const idx={code:col('code','mã','ma'),description:col('description','diễn giải','dien giai','tên công việc'),unit:col('unit','đvt','dvt'),quantity:col('quantity','khối lượng','khoi luong'),unitPrice:col('unitprice','unit_price','đơn giá','don gia')};if(idx.quantity<0||idx.unitPrice<0)throw Error('CSV cần cột quantity và unitPrice.');return rows.map((arr,i)=>{let quantity,unitPrice;try{quantity=numberVN(arr[idx.quantity]);unitPrice=numberVN(arr[idx.unitPrice]);}catch{throw Error(`Dòng ${i+2} có số không hợp lệ`);}if(quantity<0||unitPrice<0)throw Error(`Dòng ${i+2}: khối lượng/đơn giá không được âm`);return {code:idx.code<0?'':arr[idx.code],description:idx.description<0?'':arr[idx.description],unit:idx.unit<0?'':arr[idx.unit],quantity,unitPrice,total:quantity*unitPrice};});}
export function formatVND(num){return new Intl.NumberFormat('vi-VN',{style:'currency',currency:'VND',maximumFractionDigits:0}).format(num);}
export function sumBOQ(rows){return rows.reduce((sum,r)=>sum+r.total,0);}
