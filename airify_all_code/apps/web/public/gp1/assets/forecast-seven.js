'use strict';
// Future daily PM2.5 only. Never supplies current readings, AQI or exposure inputs.
(function (root, factory) {
  const api=factory();
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.AirifyForecast=api;
})(typeof window!=='undefined'?window:this, function () {
  const PHI=.8, DAY=86400000;
  const valid=v=>typeof v==='number'&&Number.isFinite(v)&&v>=0;
  const mean=values=>values.reduce((a,b)=>a+b,0)/values.length;
  const shift=(day,n)=>new Date(Date.parse(day+'T00:00:00Z')+n*DAY).toISOString().slice(0,10);
  const distance=(a,b)=>Math.round((Date.parse(a)-Date.parse(b))/DAY);
  const bangkokToday=()=>new Date().toLocaleDateString('sv-SE',{timeZone:'Asia/Bangkok'});

  function build(hourly=[],today=bangkokToday()) {
    if(!/^\d{4}-\d{2}-\d{2}$/.test(today)||!Number.isFinite(Date.parse(today)))throw Error('Invalid forecast date');
    const grouped=new Map();
    for(const row of hourly){
      if(typeof row?.time!=='string'||!/^\d{4}-\d{2}-\d{2}T\d{2}:00/.test(row.time)||!valid(row.pm))continue;
      const day=row.time.slice(0,10),hour=+row.time.slice(11,13);if(hour>23)continue;
      if(!grouped.has(day))grouped.set(day,new Map());grouped.get(day).set(hour,row.pm);
    }
    const summaries=[...grouped].sort(([a],[b])=>a.localeCompare(b)).map(([day,hours])=>({day,hours,providerHours:hours.size}));
    const completed=summaries.filter(r=>r.providerHours===24).map(r=>({...r,pm:mean([...r.hours.values()]),kind:'provider',estimatedHours:0}));
    const last=completed.at(-1);
    let filled=null;
    // Fill only an adjacent, substantially covered partial day. Sparse/gapped input stays unavailable.
    const partial=last&&summaries.find(r=>r.day===shift(last.day,1)&&r.providerHours>=12&&r.providerHours<24);
    if(partial&&last.day>=today){
      const overlap=[...partial.hours.keys()],prior=mean(overlap.map(h=>last.hours.get(h))),current=mean([...partial.hours.values()]);
      if(prior>0||current===0){
        const scale=prior>0?current/prior:1,hours=new Map(partial.hours);
        for(let h=0;h<24;h++)if(!hours.has(h))hours.set(h,last.hours.get(h)*scale);
        if([...hours.values()].every(valid))filled={...partial,hours,pm:mean([...hours.values()]),kind:'mixed',estimatedHours:24-partial.providerHours,scale};
      }
    }
    const anchors=[...completed,...(filled?[filled]:[])].slice(-3),anchor=anchors.at(-1);
    const consecutive=anchors.length===3&&distance(anchors[1].day,anchors[0].day)===1&&distance(anchors[2].day,anchors[1].day)===1;
    const canExtend=consecutive&&anchor.day>=today;
    const drift=canExtend?(anchor.pm-anchors[0].pm)/2:null;
    const rows=Array.from({length:7},(_,i)=>{
      const day=shift(today,i+1),known=completed.find(r=>r.day===day)||(filled?.day===day?filled:null);
      if(known)return{day,pm:known.pm,kind:known.kind,providerHours:known.providerHours,estimatedHours:known.estimatedHours};
      const partialHours=grouped.get(day)?.size||0,horizon=anchor?distance(day,anchor.day):0;
      // An incomplete provider day is not a reliable daily mean; use the disclosed Airify trial extension instead.
      if(canExtend&&partialHours<24&&horizon>0&&horizon<=7){
        const steps=Array.from({length:horizon},(_,j)=>PHI**(j+1)).reduce((a,b)=>a+b,0),pm=Math.max(0,anchor.pm+drift*steps);
        if(valid(pm))return{day,pm,kind:'airify',providerHours:0,estimatedHours:24,horizon};
      }
      return{day,pm:null,kind:'unavailable',providerHours:partialHours,estimatedHours:0};
    });
    return{today,rows,phi:PHI,drift,anchor:canExtend?anchor.day:null};
  }

  function render(result,{lang='th',state='live'}={}) {
    const en=lang==='en',t=(th,english)=>en?english:th,esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const number=n=>valid(n)?n.toLocaleString(en?'en-GB':'th-TH',{minimumFractionDigits:1,maximumFractionDigits:1}):'—';
    const source={provider:'Open-Meteo',mixed:'Open-Meteo + Airify',airify:t('Airify · ทดลอง','Airify · trial'),unavailable:t('ไม่มีข้อมูล','Unavailable')};
    const hasEstimate=result.rows.some(r=>r.estimatedHours>0);
    const status=state==='loading'?`<p class="af-seven-status" role="status">${t('กำลังโหลดพยากรณ์ของพื้นที่นี้…','Loading this area’s forecast…')}</p>`:state==='error'?`<p class="af-seven-status" role="status">${t('เรียกพยากรณ์ไม่ได้ ไม่มีการนำค่าของพื้นที่ก่อนหน้ามาใช้','Forecast unavailable. Previous-area values are not substituted.')}</p>`:'';
    return `<div class="af-seven" aria-label="${t('พยากรณ์ PM2.5 ล่วงหน้า 7 วัน','Seven-day PM2.5 forecast')}">
      <p class="af-seven-context">${t('ค่าเฉลี่ยรายวัน · 7 วันข้างหน้า เริ่มพรุ่งนี้','Daily averages · seven days starting tomorrow')}</p>${status}
      <div class="af-seven-rows">${result.rows.map(r=>{
        const date=new Date(r.day+'T12:00:00+07:00'),label=date.toLocaleDateString(en?'en-GB':'th-TH',{weekday:'short',day:'numeric',month:'short',timeZone:'Asia/Bangkok'});
        const detail=r.kind==='provider'?t('เฉลี่ยจากข้อมูล Open-Meteo / CAMS ครบ 24 ชั่วโมง เป็นค่าพยากรณ์จากแบบจำลอง ไม่ใช่ค่าจากสถานีตรวจวัด','Average of 24 provider hours from Open-Meteo / CAMS. Model forecast, not a station measurement.'):r.kind==='mixed'?t(`ใช้ข้อมูล Open-Meteo ${r.providerHours} ชั่วโมง และประมาณเพิ่ม ${r.estimatedHours} ชั่วโมงจากรูปแบบของวันก่อน ส่วนที่เติมเป็นการคำนวณทดลองของ Airify`,`Uses ${r.providerHours} Open-Meteo hours and ${r.estimatedHours} hours estimated from the previous day’s pattern. Filled hours are experimental Airify estimates.`):r.kind==='airify'?t('Airify คำนวณต่อจากแนวโน้มค่าเฉลี่ย 3 วันล่าสุด โดยลดแรงแนวโน้มลงวันละ 20% หากข้อมูล Open-Meteo ของวันนี้ไม่ครบ 24 ชั่วโมง จะไม่นำข้อมูลบางส่วนมาแสดงเป็นค่าเฉลี่ยรายวัน ค่านี้เป็นการทดลอง ไม่ใช่ข้อมูลพยากรณ์ที่ Open-Meteo ส่งมาสำหรับวันนี้ และยังไม่ได้ทดสอบความแม่นยำ','Airify extends the latest three daily means with trend increments damped by 20% each day. Incomplete Open-Meteo hours are not presented as a daily average. This experimental value is not a provider forecast for this date and has not been validated.'):t('ข้อมูลรายชั่วโมงไม่เพียงพอสำหรับค่าเฉลี่ยครบวัน หรือไม่มีข้อมูลพอคำนวณต่อ จึงไม่แสดงตัวเลข','Insufficient hourly coverage or trend data. No numerical forecast is shown.');
        return `<details class="af-seven-day" data-forecast-kind="${r.kind}" data-forecast-date="${r.day}"><summary><time datetime="${r.day}">${esc(label)}</time><span class="af-seven-value">${number(r.pm)}<small>µg/m³</small></span><span class="af-seven-source">${state==='loading'?t('รอข้อมูล','Pending'):source[r.kind]}</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m8 5 7 7-7 7"/></svg></summary><p>${esc(detail)}</p></details>`;
      }).join('')}</div>
      ${hasEstimate?`<p class="af-seven-note">${t('Airify เป็นสูตรทดลอง ยังไม่ได้ตรวจสอบความแม่นยำ ไม่ใช่ค่าตรวจวัดหรือการรับรองความปลอดภัย','Airify estimates are experimental and unvalidated, not measurements or a safety assessment.')}</p>`:''}
      <details class="af-seven-method"><summary>${t('วิธีคำนวณและข้อจำกัด','Method and limitations')}</summary><p>${t('เก็บค่าที่ API ให้มาทุกชั่วโมง หากวันสุดท้ายมีข้อมูลอย่างน้อย 12 ชั่วโมง จะเติมชั่วโมงที่ขาดด้วยรูปแบบเวลาเดียวกันของวันก่อน ปรับตามสัดส่วนค่าที่ทับซ้อนกัน วันที่ยังมีชั่วโมงไม่ครบ 24 ชั่วโมงและเติมจากวันก่อนหน้าไม่ได้ จะใช้แนวโน้มเฉลี่ย 3 วันล่าสุดแบบลดแรง (ตัวคูณ 0.8) เมื่อมีข้อมูลต่อเนื่องเพียงพอ ไม่มีการสุ่มค่า และไม่ใช้ค่าที่คำนวณนี้แทนค่าฝุ่นปัจจุบัน กราฟย้อนหลัง หรือผลประเมินการรับฝุ่น','Provider hours are preserved. A final day with at least 12 hours may be completed using the prior day’s same-hour pattern scaled to overlapping hours. If a date still lacks a full 24 hours and cannot be completed from the previous day, the forecast uses the latest three-day trend damped by 0.8 when enough consecutive data exists. There is no randomness. These results never replace current readings, historical charts or exposure inputs.')}</p><p>${t('สูตรยังไม่รวมฝน ลม แหล่งกำเนิดฝุ่น หรือเหตุไฟไหม้ และยังไม่ได้ประเมินความแม่นยำกับข้อมูลตรวจวัดจริง','The extension has no explicit rain, wind, emissions or fire inputs and has not been evaluated against station observations.')}</p></details>
    </div>`;
  }
  return{build,render,bangkokToday};
});
