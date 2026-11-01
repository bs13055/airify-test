'use strict';
// Mobile presentation shares the existing explorer's data and estimate engine.
// Air quality comes only from Open-Meteo/CAMS; settings remain on this device.
(() => {
  const originalUpdatePage = updatePage;
  updatePage = function () { originalUpdatePage(); window.dispatchEvent(new Event('airify:data')); };
  const forced = new URLSearchParams(location.search).get('mobile') === '1';
  if (forced) document.documentElement.classList.add('mobile-preview');
  const root = document.getElementById('mobileApp');
  const mq = matchMedia('(max-width: 1199px)');
  const desktopMq = matchMedia('(min-width: 1200px)');
  const useDesktop = () => !forced && desktopMq.matches && Boolean(window.AirifyDesktop);
  let desktopMapStyle='street';
  const storage = {
    get(key, fallback) { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } },
    set(key, value) { try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch { toast('บันทึกการตั้งค่าไม่ได้ในเบราว์เซอร์นี้'); return false; } }
  };
  const prefs = { dark:false, lang:'th', travel:true, personal:true, sharing:false, location:false, source:'live', name:'คุณแอร์ไฟ', email:'user@example.com', guest:false, ...storage.get('airify-mobile-settings', {}), source:'live' };
  const defaults = [];
  let saved = storage.get('airify-mobile-places', defaults).map(p=>({...p,example:p.example??['home','work','school'].includes(p.id)}));
  let pinning=false,pinDraft=null,pinName='',draftMarker=null,mapViewport=null;
  let initialized = false, mobileMap = null, mapRetry = null, expanded = false, allActivities = false, allRecords = false, historyDays = 7, liveBusy = false;
  let savedReadings = new Map(), savedRequest = null, mapRows = [], liveHistory = null, liveHistoryRequest = null, historyLoading = false, historyLoadError = false;
  const paths = {
    wind:'<path d="M3 8h12a3 3 0 1 0-3-3M2 12h17a3 3 0 1 1-3 3M4 16h5a3 3 0 1 1-3 3"/>',
    sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    pin:'<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="2.5"/>',
    chart:'<path d="M4 20V10m5 10V5m5 15V9m5 11V2"/>',
    user:'<circle cx="12" cy="12" r="9"/><circle cx="12" cy="9" r="3"/><path d="M6 19a6 6 0 0 1 12 0"/>',
    person:'<circle cx="12" cy="5" r="3"/><path d="M4 21v-2a8 8 0 0 1 16 0v2Z"/>',
    map:'<path d="m3 5 6-3 6 3 6-3v17l-6 3-6-3-6 3Zm6-3v17m6-14v17"/>',
    house:'<path d="m2 11 10-9 10 9M5 9v12h14V9M9 21v-8h6v8"/>',
    briefcase:'<rect x="3" y="7" width="18" height="14" rx="2"/><path d="M8 7V4h8v3M3 12c6 3 12 3 18 0m-9 0v4"/>',
    school:'<path d="m2 9 10-6 10 6-10 6Zm4 3v6c4 3 8 3 12 0v-6m4-3v9"/>',
    heart:'<path d="M20.8 4.6a5.4 5.4 0 0 0-7.7 0L12 5.8l-1.1-1.2a5.4 5.4 0 0 0-7.7 7.7L12 21l8.8-8.7a5.4 5.4 0 0 0 0-7.7Z"/><path d="M2 11h5l2-4 4 8 2-4h7"/>',
    calc:'<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M4 8h16M8 12h1m6 0h1m-8 4h1m6 0h1m-8 3h1m6 0h1"/>',
    walk:'<circle cx="14" cy="3" r="2"/><path d="m7 21 3-9 3 3-1 6M6 11l3-5 4 1 3 5h4m-9-5-1 5"/>',
    clock:'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>',
    moon:'<path d="M21 13a9 9 0 0 1-10-11A9 9 0 1 0 21 13Z"/>',
    globe:'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 9h18M3 15h18"/>',
    info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.1"/>',
    shield:'<path d="m12 2 8 3v7c0 5-8 10-8 10S4 17 4 12V5Zm-3 9 2 2 4-4"/>',
    database:'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
    right:'<path d="m9 5 7 7-7 7"/>', down:'<path d="m6 9 6 6 6-6"/>',
    locate:'<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3"/>',
    logout:'<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4m7 4 5 5-5 5M8 12h13"/>',
    settings:'<path d="m9 3 1-2h4l1 2 3 2 2 1 1 4-2 2v3l1 2-3 3-3-1-2 1-2 2-4-1-1-3-2-2-2-1V9l2-1 1-3 3-1Z"/><circle cx="12" cy="12" r="3"/>',
    bulb:'<path d="M9 18v-2a7 7 0 1 1 6 0v2Zm0 3h6"/>',
    trend:'<path d="m3 17 6-6 4 4 8-10m-7 0h7v7"/>',
    star:'<path d="m12 2 3 6 7 1-5 5 1 7-6-3-6 3 1-7-5-5 7-1Z"/>',
    calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 2v6m10-6v6M3 11h18"/>',
    leaf:'<path d="M20 3c-6 0-16 0-16 9a7 7 0 0 0 13 3c2-4 3-8 3-12ZM3 22 15 10"/>',
    search:'<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>'
  };
  paths.share='<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m9 10 6-4m-6 8 6 4"/>';
  paths.expand='<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M3 3l6 6m12-6-6 6M3 21l6-6m12 6-6-6"/>';
  paths.close='<path d="m6 6 12 12M6 18 18 6"/>';
  paths.trash='<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>';
  const icon = name => `<svg class="m-icon" viewBox="0 0 24 24" aria-hidden="true">${paths[name] || paths.info}</svg>`;
  const t = (th,en) => prefs.lang === 'en' ? en : th;
  const esc = escapeHTML;
  const num = (value,d=0) => value!==null && value!==undefined && value!=='' && Number.isFinite(+value) ? Number(value).toLocaleString(prefs.lang==='en'?'en-US':'th-TH',{maximumFractionDigits:d,minimumFractionDigits:d}) : '—';
  const savePrefs = () => storage.set('airify-mobile-settings',prefs);
  const todayDate = () => new Date().toLocaleDateString(prefs.lang==='en'?'en-GB':'th-TH',{weekday:'long',day:'numeric',month:'long'});
  const localeDate = date => new Date(date).toLocaleDateString(prefs.lang==='en'?'en-GB':'th-TH',{day:'numeric',month:'short'});
  // The shared shell is active for mobile and the approved desktop viewport.
  const useMobile = () => forced || mq.matches || useDesktop();
  const placeName = () => prefs.lang==='en' && selected.name==='นนทบุรี' ? 'Nonthaburi' : selected.name;
  const heading = (ico,title,sub='',action='') => `<div class="m-card-heading">${icon(ico)}<div><h2>${title}</h2>${sub?`<p>${sub}</p>`:''}</div>${action}</div>`;
  const textBtn = (label,action) => `<button class="m-text-btn" data-m-action="${action}">${label}${icon('right')}</button>`;
  const sourceNote = () => `<p class="m-source-note">${t('ข้อมูลแบบจำลอง Open-Meteo / CAMS ไม่ใช่เซนเซอร์ระดับถนน','Open-Meteo / CAMS model data; not street-level sensor readings.')} · ${t('ค่าประเมินไม่ใช่การวินิจฉัยสุขภาพ','Estimates are not a medical assessment.')} <a href="index.html">${t('กลับหน้าแรก','Airify home')}</a></p>`;
  const readingTime = () => {
    if(!data?.updated)return t('ยังไม่มีเวลาอ้างอิงจากผู้ให้บริการ','No provider reference time available');
    const stamp=/Z$|[+-]\d{2}:\d{2}$/.test(data.updated)?data.updated:data.updated+'+07:00';
    return t('เวลาอ้างอิง: ','Reference time: ')+new Date(stamp).toLocaleString(prefs.lang==='en'?'en-GB':'th-TH',{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Bangkok'})+t(' น. (ประเทศไทย)',' (Thailand)');
  };
  function records() {
    const rows = storage.get('airify-preview-history',[]).map(normalizeHistoryRecord).filter(r=>r.mode==='live');
    const end=new Date();
    const start=new Date(Date.now()-historyDays*86400000);
    return rows.filter(r=>r.timestamp&&new Date(r.timestamp)>=start&&new Date(r.timestamp)<=end).sort((a,b)=>(new Date(b.timestamp)-new Date(a.timestamp)));
  }
  function dailyReadings() {
    const now=Date.now(),today=new Date(now).toLocaleDateString('sv-SE',{timeZone:'Asia/Bangkok'});
    const first=new Date(Date.parse(today+'T00:00:00Z')-(historyDays-1)*86400000).toISOString().slice(0,10),grouped={};
    if(historyLoading&&liveHistory?.key!==`${selected.lat},${selected.lon}`)return [];
    if(historyLoadError&&liveHistory?.key!==`${selected.lat},${selected.lon}`)return [];
    for(const row of (liveHistory?.key===`${selected.lat},${selected.lon}`?liveHistory.hourly:data?.hourly)||[]){
      if(typeof row.time!=='string'||typeof row.pm!=='number'||!Number.isFinite(row.pm)||row.pm<0)continue;
      const day=row.time.slice(0,10),stamp=/Z$|[+-]\d{2}:\d{2}$/.test(row.time)?row.time:row.time+'+07:00',time=Date.parse(stamp);
      if(day<first||day>today||!Number.isFinite(time)||time>now)continue;
      (grouped[day]??=[]).push(row.pm);
    }
    return Object.entries(grouped).sort(([a],[b])=>a.localeCompare(b)).map(([day,values])=>({time:day+'T12:00:00+07:00',pm:values.reduce((a,b)=>a+b,0)/values.length}));
  }
  function bars(compact=false,minimumWidth=350) {
    const rows=dailyReadings();
    if(historyLoading)return `<div class="m-empty m-chart-loading" role="status" aria-live="polite">${t(`กำลังโหลดข้อมูลย้อนหลัง ${historyDays} วัน…`,`Loading ${historyDays} days of history…`)}</div>`;
    if(historyLoadError&&!rows.length)return `<div class="m-empty" role="status">${t('โหลดข้อมูลย้อนหลังไม่สำเร็จ','Could not load historical data.')}<br><button class="m-text-btn" data-m-action="retry-history">${t('ลองใหม่','Retry')}</button></div>`;
    if(!rows.length)return `<div class="m-empty">${t('ยังไม่มีข้อมูลย้อนหลังสำหรับพื้นที่นี้','No historical data for this place yet.')}</div>`;
    const wide=rows.length>7,w=Math.max(minimumWidth,rows.length*46+40),h=compact?(minimumWidth>=700?125:150):176,L=30,R=10,T=24,B=42,ymax=Math.max(50,Math.ceil(Math.max(...rows.map(r=>r.pm))/10)*10),cw=(w-L-R)/rows.length,bw=Math.min(26,cw*.58);
    const dateLabel=time=>new Date(time).toLocaleDateString(prefs.lang==='en'?'en-GB':'th-TH',{day:'numeric',month:'short',timeZone:'Asia/Bangkok'});
    let axis=`<svg class="m-chart-axis" viewBox="0 0 ${L} ${h}" preserveAspectRatio="none" aria-hidden="true"><text x="1" y="12" fill="var(--m-muted)" font-size="8">µg/m³</text>`;
    let out=`<div class="m-chart-frame"><div class="m-chart-scroll" ${wide?`tabindex="0" role="region" aria-label="${t('กราฟย้อนหลัง เลื่อนแนวนอนเพื่อดูทุกวัน','History chart; scroll horizontally to view every day')}"`:''}><svg class="m-chart" style="min-width:${wide?w-L:0}px" viewBox="${L} 0 ${w-L} ${h}" role="img" aria-label="${t('กราฟค่าเฉลี่ย PM2.5 ย้อนหลัง หน่วยไมโครกรัมต่อลูกบาศก์เมตร','Historical daily average PM2.5 chart, micrograms per cubic metre')}">`;
    if(minimumWidth>=700){for(const [low,high,color] of [[0,20,'#5fd6b0'],[20,30,'#f9d847'],[30,40,'#ffb23b'],[40,ymax,'#ea8ca8']]){const bottom=Math.min(ymax,low),top=Math.min(ymax,high);if(top>bottom)out+=`<rect x="${L}" y="${h-B-(h-T-B)*top/ymax}" width="${w-L-R}" height="${(h-T-B)*(top-bottom)/ymax}" fill="${color}" opacity=".12"/>`;}}
    for(let i=0;i<=5;i++){const y=h-B-(h-T-B)*i/5;out+=`<path d="M${L} ${y}H${w-R}" fill="none" stroke="var(--m-line)" stroke-dasharray="1.4 2"/>`;axis+=`<text x="${L-7}" y="${y+3}" text-anchor="end" font-size="9" fill="var(--m-muted)">${Math.round(ymax*i/5)}</text>`;}
    for(const [i,row] of rows.entries()){
      const x=L+cw*(i+.5),height=(h-T-B)*row.pm/ymax,y=h-B-height,color=row.pm<=20?'#65ce80':row.pm<=30?'#ffd02d':'#ff9c25';
      const weekday=prefs.lang==='en'?new Date(row.time).toLocaleDateString('en-GB',{weekday:'short',timeZone:'Asia/Bangkok'}):['อา.','จ.','อ.','พ.','พฤ.','ศ.','ส.'][new Date(row.time.slice(0,10)+'T00:00:00Z').getUTCDay()];
      const fullDate=new Date(row.time).toLocaleDateString(prefs.lang==='en'?'en-GB':'th-TH',{weekday:'long',day:'numeric',month:'long',year:'numeric',timeZone:'Asia/Bangkok'});
      out+=`<g class="m-chart-day" data-chart-date="${row.time.slice(0,10)}"><title>${esc(fullDate)} · ${num(row.pm,1)} µg/m³</title><rect x="${x-bw/2}" y="${y}" width="${bw}" height="${height}" rx="4" fill="${color}"/><text x="${x}" y="${y-5}" text-anchor="middle" font-size="10" font-weight="700" fill="var(--m-ink)">${num(row.pm)}</text><text class="m-chart-date" x="${x}" y="${h-23}" text-anchor="middle" font-size="9" fill="var(--m-ink)">${esc(dateLabel(row.time))}</text><text class="m-chart-weekday" x="${x}" y="${h-7}" text-anchor="middle" font-size="9" fill="var(--m-muted)">${weekday}</text></g>`;
    }
    return out+'</svg></div>'+axis+'</svg></div>'+(wide?`<p class="m-chart-hint">${esc(dateLabel(rows[0].time))} – ${esc(dateLabel(rows.at(-1).time))} · ${t('เลื่อนแนวนอนเพื่อดูครบ '+rows.length+' วัน','Scroll horizontally to view all '+rows.length+' days')}</p>`:'');
  }
  function alignChartAxes(){for(const frame of root.querySelectorAll('.m-chart-frame'))frame.querySelector('.m-chart-axis').style.height=frame.querySelector('.m-chart').getBoundingClientRect().height+'px';}
  function locationRow(){return `<div class="m-location"><button class="m-place-trigger" data-m-action="search" aria-label="${t('เลือกพื้นที่','Select area')}">${icon('pin')}<span><strong>${esc(placeName())}${icon('down')}</strong><small>${todayDate()} · ${t('พื้นที่ที่เลือกขณะนี้','Selected area')}</small></span></button><button class="m-locate" data-m-action="locate">${icon('locate')}${t('ตำแหน่งของฉัน','My location')}</button></div>`;}
  function hero(){
    const pm=data?.pm, b=band(data?.aqi),color=b.color==='#21a56d'?'background:linear-gradient(130deg,#248253,#21744a);color:#fff':b.color==='#e7a116'?'':'background:linear-gradient(130deg,#b45714,#a34b12);color:#fff';
    const advice=!data?t('ยังไม่มีข้อมูลคุณภาพอากาศ','No air quality data available'):t('ติดตามค่าฝุ่นและประกาศในพื้นที่ก่อนทำกิจกรรมกลางแจ้ง','Check local air readings and advisories before outdoor activities.');
    return `<section class="m-hero" style="${color}" aria-label="${t('คุณภาพอากาศวันนี้','Air quality today')}"><svg class="m-hero-waves" viewBox="0 0 400 160" preserveAspectRatio="none" aria-hidden="true"><path d="M0 18Q65 150 118 66T214 85T311 60T400 74V160H0Z"/></svg><div class="m-hero-top"><span>${t('คุณภาพอากาศ ณ พื้นที่ที่เลือก','Air quality at the selected area')}</span><b class="m-air-band">${!data?t('รอข้อมูล','Waiting'):data.aqi==null?t('ไม่มี AQI','AQI unavailable'):prefs.lang==='en'?(data.aqi<=50?'Good':data.aqi<=100?'Moderate':'Elevated'):b.label}</b></div><div class="m-pm-line"><strong>${data?num(pm,1):'—'}</strong><span>µg/m³ PM2.5</span></div><div class="m-pm-track"><span style="width:${data?Math.min(100,Math.max(8,pm/55*100)):0}%"></span></div><p class="m-hero-advice">${advice}<button class="m-info-button" data-m-action="air-info" aria-label="${t('เกี่ยวกับค่าฝุ่น','About this reading')}">${icon('info')}</button></p><div class="m-hero-stats"><div class="m-hero-stat">${icon('sun')}<span><small>${t('เทียบกับเมื่อวาน','Yesterday')}</small><b>${comparisonText()}</b></span></div><div class="m-hero-stat">${icon('leaf')}<span><small>${t('ระดับ AQI (US)','US AQI')}</small><b>${data?num(data.aqi):'—'} · ${t('ดัชนี','Index')}</b></span></div><div class="m-hero-stat">${icon('pin')}<span><small>${t('แหล่งข้อมูล','Data source')}</small><b>Open-Meteo / CAMS</b></span></div></div><p class="m-reading-time">${readingTime()}</p></section>`;
  }
  function comparisonText(){const cutoff=Date.now()-86400000,rows=(data?.hourly||[]).filter(h=>Math.abs(new Date(h.time+'+07:00').getTime()-cutoff)<3600000);const old=rows[0]?.pm;return old>0&&data?`${data.pm>old?'+':''}${num((data.pm/old-1)*100)}%`:'—';}
  const recommendations=[['running','🏃','วิ่งกลางแจ้ง','Outdoor running','ทำได้ แต่ควรลดเวลาและสังเกตอาการ','Reduce time and pay attention to symptoms.'],['motorbike','🛵','เดินทางไปทำงาน','Commute to work','ทำได้ แต่ควรสวมหน้ากาก','Consider a well-fitting mask.'],['walking','👦','พาเด็กออกนอกบ้าน','Take children outside','ทำได้ แต่ควรลดเวลา','Keep outdoor time shorter.'],['indoor','🪟','เปิดหน้าต่าง','Open the windows','ทำได้ แต่ควรลดเวลาในช่วงที่ค่าฝุ่นสูง','Limit ventilation during high pollution.'],['walking','🌳','เดินเล่นในสวน','Walk in the park','ลองเปรียบเทียบช่วงเวลาที่ค่าฝุ่นต่ำกว่า','Compare times with lower pollution.'],['cycling','🚴','ปั่นจักรยาน','Go cycling','เลือกเส้นทางห่างจากการจราจรหนาแน่น','Choose a route away from busy traffic.']];
  const recommendationDetails=[
    ['ในแบบจำลองของ Airify การวิ่งใช้อัตราการหายใจสูงกว่าการเดิน เมื่อใช้ค่าฝุ่นและระยะเวลาเท่ากัน จึงได้ค่าประมาณการรับฝุ่นมากกว่า ลองเปรียบเทียบกิจกรรมหรือระยะเวลาที่ต่างกันก่อนวางแผน','Airify assigns running a higher breathing rate than walking. With the same PM2.5 and duration, the model therefore estimates a larger inhaled amount. Compare activities and durations when planning.','ปุ่มด้านล่างจะเลือกวิ่งกลางแจ้ง โดยยังปรับระยะเวลาได้ในแบบประเมิน','The button selects outdoor running. You can adjust duration in the estimator.'],
    ['การเดินทางแต่ละแบบมีสมมติฐานต่างกัน เช่น การขี่มอเตอร์ไซค์กับการอยู่ในรถยนต์ ลองเลือกวิธีเดินทางและระยะเวลาที่ใกล้เคียงกับแผนของคุณ เพื่อดูว่าผลประเมินต่างกันอย่างไร','Travel modes use different assumptions, such as riding a motorbike versus being in a car. Compare your planned mode and duration in the estimator.','รายการนี้เริ่มที่ขี่มอเตอร์ไซค์ คุณเปลี่ยนเป็นอยู่ในรถยนต์หรือเดินทั่วไปได้','This starts with motorbike travel. You can switch to a car or walking.'],
    ['ใช้ข้อมูล PM2.5 ของพื้นที่ประกอบการวางแผนสถานที่และเวลาที่จะออกไป รายการนี้ยังไม่มีแบบจำลองอัตราการหายใจเฉพาะเด็ก จึงไม่ควรอ่านผลเป็นปริมาณฝุ่นที่เด็กได้รับจริง','Use local PM2.5 information to help plan where and when to go outside. This preview has no child-specific breathing model, so the result does not represent a child’s actual exposure.','ปุ่มด้านล่างเปิดการเดินทั่วไปเพื่อเปรียบเทียบสถานการณ์เท่านั้น','The button opens general walking for scenario comparison only.'],
    ['ค่าฝุ่นในพื้นที่ที่แสดงเป็นข้อมูลอากาศภายนอก จึงยังบอกค่าฝุ่นภายในห้องหรือผลจากการเปิดหน้าต่างโดยตรงไม่ได้ ใช้ข้อมูลนี้ประกอบการพิจารณาช่วงเวลาเปิดหน้าต่าง','The displayed PM2.5 describes outdoor air. It does not directly measure indoor air or the effect of opening a window. Use it as context when considering ventilation timing.','แบบประเมินจะเลือกอยู่ในอาคารและใช้ปัจจัยอาคารตามสมมติฐานของเว็บ ไม่ใช่การจำลองหน้าต่างหรือการระบายอากาศจริง','The estimator selects indoors using the site’s assumed indoor factor. It does not simulate a window or actual ventilation.'],
    ['ค่าฝุ่นที่แสดงอ้างอิงพิกัดพื้นที่ที่เลือก ไม่ได้วัดแยกทุกจุดภายในสวน ลองเปรียบเทียบพื้นที่และระยะเวลาเดินที่ต้องการผ่านแบบประเมิน','The PM2.5 value refers to the selected area, not every spot within a park. Compare locations and walking durations using the estimator.','ปุ่มด้านล่างจะเลือกเดินทั่วไปในสภาพแวดล้อมกลางแจ้ง','The button selects walking outdoors.'],
    ['ในแบบจำลอง การปั่นจักรยานใช้อัตราการหายใจต่างจากการเดิน ผลประเมินยังขึ้นกับค่าฝุ่นและระยะเวลาที่เลือก และไม่ได้คำนวณฝุ่นตามเส้นทางทุกช่วงถนน','The model assigns cycling a different breathing rate from walking. The estimate also depends on PM2.5 and duration; it does not calculate pollution along every segment of a route.','ปุ่มด้านล่างจะเลือกปั่นจักรยานกลางแจ้ง โดยปรับเวลาได้ก่อนบันทึก','The button selects outdoor cycling. Adjust duration before saving.']
  ];
  function openRecommendation(index){
    const row=recommendations[index],detail=recommendationDetails[index];if(!row||!detail)return;
    const reading=data?`${esc(placeName())} · PM2.5 ${num(data.pm,1)} µg/m³`:t('ยังไม่มีค่าฝุ่นของพื้นที่นี้ กรุณารอโหลดข้อมูลก่อนประเมิน','No PM2.5 reading for this area yet. Wait for data before estimating.');
    openSheet(t(row[2],row[3]),`<div class="m-recommendation-detail"><p>${reading}</p><h3>${t('ทำไมถึงมีคำแนะนำนี้','Why this recommendation?')}</h3><p>${t(detail[0],detail[1])}</p><h3>${t('ลองเปรียบเทียบในแบบประเมิน','Compare in the estimator')}</h3><p>${t(detail[2],detail[3])}</p><button type="button" class="m-primary" data-m-act="${row[0]}">${t(index===2?'ลองเปรียบเทียบแบบเดินทั่วไป':'ลองประเมินกิจกรรมนี้',index===2?'Compare general walking':'Estimate this activity')}</button></div>`);
  }
  function applyRecommendationActivity(id){closeSheet();if(tab!=='today')navigate('today');document.getElementById('activity').value=id;document.getElementById('environment').value=id==='indoor'?'indoor':'outdoor';updateEstimate();document.getElementById('m-activity').value=id;refreshEstimate();document.getElementById('m-estimator').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth',block:'center'});}
  function activities(){const good=Number.isFinite(data?.aqi)&&data.aqi<=50;return `<section class="m-card">${heading('heart',t('คำแนะนำสำหรับคุณวันนี้','Your daily activity guide'),'',textBtn(allActivities?t('แสดงน้อยลง','Show less'):t('ดูทั้งหมด','See all'),'activities'))}<div class="m-activities">${recommendations.slice(0,allActivities?6:4).map(([id,emoji,th,en,detail,detailEn],index)=>`<button type="button" class="m-activity" data-m-recommendation="${index}" aria-haspopup="dialog" aria-label="${t('อ่านคำอธิบาย: '+th,'Read explanation: '+en)}"><span class="m-emoji" aria-hidden="true">${emoji}</span><span class="m-activity-copy"><b>${t(th,en)}</b><small>${prefs.personal?t(detail,detailEn):t('เลือกเพื่ออ่านคำอธิบาย','Select to read the explanation')}</small></span><span class="m-caution">${data?.aqi==null?t('รอข้อมูล','Pending'):good?t('พอเหมาะ','Suitable'):t('ควรระวัง','Take care')}</span>${icon('right')}</button>`).join('')}</div></section>`;}
  function estimator(){const act=document.getElementById('activity').value,minutes=+document.getElementById('duration').value,value=document.getElementById('exposureValue').textContent,ratio=data?RATES[act]*ENV_FACTOR[document.getElementById('environment').value]*MASK_FACTOR[document.getElementById('mask').value]/.5:0;return `<section class="m-card" id="m-estimator">${heading('calc',t('ประเมินการรับฝุ่นของคุณ','Your exposure estimate'),t('เลือกกิจกรรมและเวลา เพื่อประมาณการรับฝุ่น','Choose an activity and duration to compare estimated inhaled PM2.5.'))}<div class="m-estimate-selects"><label class="m-select-wrap">${icon('walk')}<select id="m-activity" aria-label="${t('กิจกรรมสำหรับประเมิน','Estimate activity')}">${[['walking','เดินทั่วไป','Walking'],['running','วิ่งกลางแจ้ง','Running'],['cycling','ปั่นจักรยาน','Cycling'],['motorbike','ขี่มอเตอร์ไซค์','Motorbike'],['car','อยู่ในรถยนต์','In a car'],['indoor','อยู่ในอาคาร','Indoors']].map(([v,th,en])=>`<option value="${v}" ${v===act?'selected':''}>${t(th,en)}</option>`).join('')}</select></label><label class="m-select-wrap">${icon('clock')}<select id="m-duration" aria-label="${t('ระยะเวลาสำหรับประเมิน','Estimate duration')}">${[10,20,30,45,60,90,120,180].map(v=>`<option value="${v}" ${v===minutes?'selected':''}>${v} ${t('นาที','min')}</option>`).join('')}</select></label></div><div class="m-estimate-result" aria-live="polite"><div><small>${t('คุณอาจได้รับฝุ่นประมาณ','Estimated inhaled PM2.5')}</small><strong id="m-exposure">${value} <span>µg</span></strong></div><div class="m-estimate-relative">${icon('chart')}<span><small>${t('เทียบกับนั่งพัก','Compared to rest')}</small><b id="m-relative">${data?num(ratio,1):'—'} ${t('เท่า','×')}</b></span><button class="m-info-button" data-m-action="estimate-info" aria-label="${t('วิธีคำนวณ','How this is calculated')}">${icon('info')}</button></div></div><div class="m-estimate-footer"><small>${t('ค่าประมาณตามสมมติฐาน','A scenario estimate')}</small><button class="m-text-btn" data-m-action="save-estimate">${t('บันทึกสถานการณ์ +','Save scenario +')}</button></div></section>`;}
  function sevenDayCard(){return `<section class="m-card" id="m-forecast">${heading('calendar',t('พยากรณ์ PM2.5 ล่วงหน้า 7 วัน','Seven-day PM2.5 forecast'),esc(placeName()))}${sevenDayForecastMarkup(prefs.lang)}</section>`;}
  function today(){return `<h1 class="m-visually-hidden">${t('คุณภาพอากาศวันนี้','Air quality today')}</h1>${locationRow()}${hero()}${sevenDayCard()}${activities()}${estimator()}<section class="m-card">${heading('chart',t('แนวโน้ม PM2.5 ในพื้นที่','PM2.5 trend in the area'),'',textBtn(t('ดูประวัติ','History'),'history'))}${bars(true)}</section>${sourceNote()}`;}
  function places(){
    return `<h1 class="m-visually-hidden">${t('พื้นที่และแผนที่คุณภาพอากาศ','Places and air quality map')}</h1>${locationRow()}
      <section class="m-card m-map-card" id="m-map-section">
        ${heading('map',t('แผนที่คุณภาพอากาศรอบตัว','Air quality around you'),t('หมุดสีน้ำเงินคือสถานที่ที่บันทึก · แตะแผนที่เพื่อเพิ่มหมุด','Blue pins are saved places · tap the map to add a pin'),textBtn(expanded?t('ย่อแผนที่','Collapse'):t('ดูทั้งหมด','Expand'),'expand-map'))}
        <div class="m-map-wrap ${expanded?'expanded':''}">
          <div id="m-map" class="m-map-canvas" aria-label="${t('แผนที่คุณภาพอากาศและหมุดสถานที่','Air quality and saved places map')}"><div class="m-map-fallback">${t('กำลังโหลดแผนที่…','Loading map…')}</div></div>
          <form class="m-pin-editor" id="m-pin-form" ${pinning?'':'hidden'}>
            <b>${icon('pin')}${t('ปักหมุดสถานที่ใหม่','Pin a new place')}</b>
            <p>${t('แตะจุดบนแผนที่ หรือลากหมุดเพื่อปรับตำแหน่ง','Tap the map or drag the pin to refine its position.')}</p>
            <button type="button" class="m-pin-center" data-m-action="pin-center">${icon('locate')}${t('เลือกจุดกลางแผนที่','Use map center')}</button>
            <label for="m-pin-name">${t('ชื่อสถานที่','Place name')}</label>
            <input type="text" id="m-pin-name" maxlength="40" placeholder="${t('เช่น บ้าน ที่ทำงาน หรือสวนใกล้บ้าน','e.g. Home, Work or a nearby park')}" value="${esc(pinName)}" required>
            <output id="m-pin-coordinates" aria-live="polite">${pinDraft?coordinateText(pinDraft):t('ยังไม่ได้เลือกพิกัด','No coordinates selected yet')}</output>
            <div class="m-pin-editor-actions"><button type="button" data-m-action="cancel-pin">${t('ยกเลิก','Cancel')}</button><button type="submit" id="m-save-pin" ${pinDraft?'':'disabled'}>${t('บันทึกหมุด','Save pin')}</button></div>
            <small>${t('เก็บหมุดเฉพาะในเบราว์เซอร์เครื่องนี้ ไม่ได้ติดตามตำแหน่งต่อเนื่อง','Pins stay in this browser. Your location is not tracked continuously.')}</small>
          </form>
          <button class="m-map-cta" data-m-action="search">${icon('map')}${t('สำรวจแผนที่พื้นที่ใกล้เคียง','Explore nearby areas')}${icon('right')}</button>
        </div>
      </section>
      <section class="m-card">${heading('star',t('สถานที่ที่คุณบันทึกไว้','Your saved places'),'',textBtn(t('จัดการ','Manage'),'manage-places'))}
        <button class="m-add-pin" data-m-action="start-pin">${icon('pin')}${t('ปักหมุดสถานที่ใหม่','Pin a new place')}<span aria-hidden="true">＋</span></button>
        <div class="m-saved-places">${saved.map(p=>{
          const pm=savedReadings.get(`${p.lat},${p.lon}`),name=prefs.lang==='en'?(p.en||p.name):p.name;
          return `<div class="m-saved-place-row"><button class="m-saved-place" data-m-place="${esc(p.id)}"><span class="m-tile-icon">${icon(p.icon)}</span><span class="m-activity-copy"><b>${esc(name)}</b><small>${p.example?t('หมุดเริ่มต้น · ','Starter pin · '):''}${esc(p.sub||coordinateText(p))}</small></span><span class="m-place-reading"><b style="${Number.isFinite(pm)&&pm>35?'background:#ff8416':Number.isFinite(pm)&&pm<20?'background:#4ec45f':''}">${Number.isFinite(pm)?num(pm,1):'—'}</b><span>µg/m³<small>${Number.isFinite(pm)?t('ค่าฝุ่น PM2.5','PM2.5'):t('ไม่มีข้อมูล','Unavailable')}</small></span></span></button><button class="m-delete-pin" data-m-delete-place="${esc(p.id)}" aria-label="${t('ลบหมุด ','Delete pin ')}${esc(name)}">${icon('trash')}</button></div>`;
        }).join('')||`<p class="m-empty">${t('ยังไม่มีหมุดที่บันทึกไว้<br>แตะแผนที่หรือกดปักหมุดสถานที่ใหม่เพื่อเริ่มต้น','No saved pins.<br>Tap the map or choose Pin a new place to get started.')}</p>`}</div>
      </section>
      <section class="m-card">${heading('chart',t('สรุปคุณภาพอากาศในพื้นที่ของคุณ','Your local air quality summary'))}<div class="m-area-summary">${icon('pin')}<div><b>${esc(placeName())} · ${t('คุณภาพอากาศวันนี้','Air quality today')}</b><p>${t('ค่าฝุ่นเป็นข้อมูลแบบจำลองตามพิกัดที่เลือก ไม่ใช่การวัดฝุ่นด้วยมือถือ','Readings are spatial model estimates at selected coordinates, not measurements from your phone.')}</p></div><div class="m-area-change">${comparisonText()}<small>${t('จากเมื่อวาน','vs. yesterday')}</small></div></div></section>${sourceNote()}`;
  }
  function historyView(chartWidth=350){const values=dailyReadings(),avg=values.length?values.reduce((a,b)=>a+b.pm,0)/values.length:null,rows=records(),sum=rows.reduce((a,r)=>a+Number(r.value||0),0),mins=rows.reduce((a,r)=>a+Number(r.minutes||0),0),recordDays=historyDays,averageLabel=historyLoading?t('กำลังโหลดข้อมูลย้อนหลัง…','Loading historical data…'):historyLoadError?t('ข้อมูลย้อนหลังโหลดไม่สำเร็จ','Historical data unavailable'):t(`ค่าเฉลี่ย ${values.length} วัน`,`${values.length}-day average`);return `<div class="m-history-heading"><div><h1>${t('ประวัติ','History')}</h1><p>${t('ดูข้อมูลคุณภาพอากาศและการรับฝุ่นของคุณย้อนหลัง','Review air quality and your exposure history')}</p></div><label class="m-select-wrap">${icon('calendar')}<select id="m-history-days" aria-label="${t('ช่วงเวลาประวัติ','History period')}"><option value="7" ${historyDays===7?'selected':''}>${t('7 วันที่ผ่านมา','Last 7 days')}</option><option value="30" ${historyDays===30?'selected':''}>${t('30 วันที่ผ่านมา','Last 30 days')}</option></select></label></div><section class="m-card">${heading('chart',t('แนวโน้ม PM2.5 ในพื้นที่','PM2.5 trend in the area'),t(`ค่าเฉลี่ยรายวันในช่วง ${historyDays} วันที่ผ่านมา`,`Daily averages over the last ${historyDays} days`),textBtn(t('ดูรายละเอียด','Details'),'chart-details'))}${bars(false,chartWidth)}<div class="m-mini-summary"><div><small>${averageLabel}</small><strong>${avg===null?'—':num(avg,1)} <span>µg/m³</span></strong></div><div><small>${t('แนวโน้ม','Trend')}</small><strong class="m-change">${t('ข้อมูลแบบจำลอง','Model data')}</strong><small>${t('ไม่มีการเติมค่าที่ขาด','Missing values stay empty')}</small></div><div><small>${t('คุณภาพอากาศโดยรวม','Overall air quality')}</small><span class="m-badge">${avg===null||data?.aqi==null?'—':prefs.lang==='en'?(data?.aqi<=50?'Good':data?.aqi<=100?'Moderate':'Elevated'):band(data?.aqi).label}</span><small>${t('AQI (US) ปัจจุบัน','Current US AQI')}</small></div></div></section><section class="m-card">${heading('person',t('แดชบอร์ดการรับฝุ่นส่วนตัว','Your personal exposure dashboard'),t('ดูประวัติกิจกรรมและปริมาณฝุ่นที่คุณอาจได้รับ','Your saved activities and estimated exposure'))}<div class="m-segment">${[7,30].map(v=>`<button data-m-range="${v}" class="${historyDays===v?'active':''}">${v} ${t('วัน','days')}</button>`).join('')}</div><div class="m-dashboard-totals"><div>${icon('chart')}<span><small>${t('ปริมาณฝุ่นที่คุณอาจได้รับ','Estimated inhaled PM2.5')}</small><strong>${num(sum,1)} <span>µg</span></strong><small>${t('เฉลี่ยวันละ','Daily average')} ${num(sum/recordDays,1)} µg</small></span></div><div>${icon('clock')}<span><small>${t('เวลาออกอาคารรวม','Total activity time')}</small><strong>${Math.floor(mins/60)} ${t('ชม.','h')} ${mins%60} ${t('นาที','min')}</strong><small>${t('เฉลี่ยวันละ','Daily average')} ${Math.round(mins/recordDays)} ${t('นาที','min')}</small></span></div></div><div class="m-subheading"><h3>${t('ประวัติกิจกรรม','Activity history')}</h3>${textBtn(allRecords?t('แสดงน้อยลง','Show less'):t('ดูทั้งหมด','See all'),'all-records')}</div><div class="m-history-entries">${rows.slice(0,allRecords?rows.length:3).map(r=>`<button class="m-history-entry" data-m-record="${esc(r.id||r.timestamp||r.at)}"><span class="m-emoji" aria-hidden="true">${r.emoji||'🚶'}</span><span class="m-activity-copy"><b>${esc(prefs.lang==='en'?(r.en||r.activity):r.activity)}</b><small>${esc(r.timestamp?localeDate(r.timestamp):r.at)} · ${esc(r.minutes)} ${t('นาที','min')}</small></span><span class="m-history-value"><small>${t('คาดว่ารับฝุ่น','Estimated')}</small><b>${num(r.value,1)} µg</b></span>${icon('right')}</button>`).join('')||`<div class="m-empty">${t('ยังไม่มีประวัติที่บันทึกไว้<br>เลือกกิจกรรมในแท็บวันนี้ แล้วกดบันทึกสถานการณ์','No saved activity yet.<br>Save a scenario from the Today tab.')}</div>`}</div></section><section class="m-card">${heading('bulb',t('ข้อมูลเชิงลึกสำหรับคุณ','Insights for you'),'',textBtn(t('ดูคำแนะนำทั้งหมด','All guidance'),'insights'))}<div class="m-insight">${icon('trend')}<div><b>${t('เปรียบเทียบสถานการณ์ของคุณ','Compare your activity scenarios')}</b><p>${t('ใช้ประวัติที่คุณบันทึกเพื่อเปรียบเทียบกิจกรรมและเวลา โดยค่าประมาณนี้ไม่ใช่ความเสี่ยงทางการแพทย์','Compare saved activities and durations. These estimates do not measure medical risk.')}</p></div></div></section>${sourceNote()}`;}

  function refreshEstimate(){
    const value=document.getElementById('exposureValue').textContent;
    const act=document.getElementById('activity').value;
    const ratio=data?RATES[act]*ENV_FACTOR[document.getElementById('environment').value]*MASK_FACTOR[document.getElementById('mask').value]/.5:0;
    const output=document.getElementById('m-exposure'),relative=document.getElementById('m-relative');
    if(output)output.innerHTML=esc(value)+' <span>µg</span>';
    if(relative)relative.textContent=(data?num(ratio,1):'—')+' '+t('เท่า','×');
  }
  function setting(id,ico,title,sub,checked,kind=''){return `<div class="m-setting-row ${kind}"><span class="m-tile-icon">${icon(ico)}</span><span class="m-activity-copy"><b>${title}</b><small>${sub}</small></span><label class="m-switch"><input type="checkbox" role="switch" id="m-${id}" data-m-setting="${id}" aria-label="${title}" ${checked?'checked':''}><span class="m-switch-track"></span></label></div>`;}
  function profile(){return `<section class="m-card m-profile-card"><button class="m-profile-main" style="border:0;background:none;width:100%;text-align:left" data-m-action="edit-profile"><span class="m-avatar" aria-hidden="true">👨🏻</span><span><p>${t('สวัสดีครับ','Hello,')}</p><h1>${prefs.guest?t('ผู้เยี่ยมชม','Guest'):esc(prefs.name)}</h1><small>${prefs.guest?t('ใช้งานได้โดยไม่ต้องสมัคร','Explore without signing up'):esc(prefs.email)}</small></span>${icon('right')}</button><button class="m-logout" data-m-action="logout">${icon('logout')}${prefs.guest?t('กลับสู่บัญชีตัวอย่าง','Use demo profile'):t('ออกจากบัญชีตัวอย่าง','Leave demo profile')}</button></section><section class="m-card m-settings-card">${heading('settings',t('การตั้งค่าแอป','App settings'),t('ปรับแต่งการใช้งานให้เหมาะกับคุณ','Make Airify work for you'))}${setting('dark','moon',t('โหมดมืด','Dark mode'),t('เปลี่ยนธีมแอปเป็นโหมดมืดเพื่อถนอมสายตา','Switch to a darker appearance'),prefs.dark)}<div class="m-setting-row"><span class="m-tile-icon">${icon('globe')}</span><span class="m-activity-copy"><b>${t('ภาษา','Language')}</b><small>${t('เลือกภาษาที่ใช้ในแอป','Choose the app language')}</small></span><label class="m-select-wrap"><select id="m-language" aria-label="${t('ภาษา','Language')}"><option value="th" ${prefs.lang==='th'?'selected':''}>ภาษาไทย</option><option value="en" ${prefs.lang==='en'?'selected':''}>English</option></select></label></div><div class="m-setting-row"><span class="m-tile-icon">${icon('info')}</span><span class="m-activity-copy"><b>${t('เวอร์ชันแอป','App version')}</b><small>${t('เวอร์ชันปัจจุบันของ Airify Health','Current Airify Health version')}</small></span><span class="m-setting-meta">1.0.0</span></div></section><section class="m-card m-settings-card">${heading('shield',t('การอนุญาตและความเป็นส่วนตัว','Permissions & privacy'),t('จัดการข้อมูลและการเข้าถึงเพื่อประสบการณ์ที่ดียิ่งขึ้น','Manage access and data on this device'))}${setting('location','pin',t('การเข้าถึงตำแหน่งที่ตั้ง','Location access'),t('ขอสิทธิ์เมื่อเปิดใช้ ไม่ติดตามตำแหน่งเบื้องหลัง','Requested when enabled; no background tracking'),prefs.location,'location')}${setting('travel','clock',t('บันทึกประวัติการเดินทาง','Save activity history'),t('จัดเก็บเฉพาะกิจกรรมที่คุณกดบันทึกในเครื่องนี้','Store only scenarios you explicitly save on this device'),prefs.travel,'travel')}${setting('personal','chart',t('คำแนะนำส่วนบุคคล','Personalized guidance'),t('ใช้กิจกรรมที่เลือกเพื่อแสดงคำแนะนำที่เกี่ยวข้อง','Adapt guidance to the activity you select'),prefs.personal,'personal')}</section><section class="m-card m-settings-card">${heading('database',t('การแบ่งปันข้อมูล','Data sharing'),t('ช่วยให้เราพัฒนา Airify Health ได้ดียิ่งขึ้น','Preferences for a better Airify Health'))}<div class="m-sharing-box">${setting('sharing','chart',t('ส่งข้อมูลแบบไม่ระบุตัวตน','Anonymous usage data'),t('เป็นตัวอย่างการตั้งค่า ยังไม่มีการส่งข้อมูลออกจากเครื่อง','Preference preview only; no analytics are transmitted'),prefs.sharing)}${textBtn(t('ดูรายละเอียดเพิ่มเติม','Learn more'),'privacy')}</div></section><section class="m-card m-settings-card">${heading('leaf',t('แหล่งข้อมูลคุณภาพอากาศ','Air quality data source'),t('ค่าปัจจุบันจาก Open-Meteo / CAMS','Current readings from Open-Meteo / CAMS'))}<p>${t('ข้อมูลคุณภาพอากาศจาก Open-Meteo / CAMS พร้อมพยากรณ์ 7 วัน โดยระบุแหล่งข้อมูลและค่าประมาณเชิงทดลองของ Airify สำหรับแต่ละวัน','Air quality data from Open-Meteo / CAMS with a seven-day forecast. Each day identifies its data source and any experimental Airify estimate.')}</p><div class="m-segment"><button data-m-source="live" ${liveBusy||mode==='loading'?'disabled':''}>${mode==='loading'?t('กำลังโหลด…','Loading…'):t('อัปเดตข้อมูล','Refresh data')}</button><button data-m-action="air-info">${t('เกี่ยวกับข้อมูล','About data')}</button></div></section>${sourceNote()}`;}
  function render(){
    const scroll=window.scrollY;
    const focused=root.contains(document.activeElement)?document.activeElement:null,focusId=focused?.id,focusTab=focused?.dataset.mTab,focusMap=focused?.dataset.dMap,searchValue=focusId==='d-search'?focused.value:'';
    if(mobileMap){const c=mobileMap.getCenter();mapViewport={lat:c.lat,lon:c.lng,zoom:mobileMap.getZoom()};mobileMap.stop();mobileMap.remove();mobileMap=null;draftMarker=null;} clearTimeout(mapRetry);
    root.classList.toggle('desktop-mode',useDesktop());
    document.documentElement.classList.toggle('desktop-active',useDesktop());
    root.dataset.theme=prefs.dark?'dark':'light';document.body.dataset.airifyTheme=prefs.dark?'dark':'light';root.lang=prefs.lang;
    root.innerHTML=useDesktop()?window.AirifyDesktop.render({t,icon,esc,num,heading,textBtn,selected,data,mode,prefs,tab,historyDays,expanded,mapStyle:desktopMapStyle,mapRows,cities:CITIES,dailyReadings,records,comparisonText,readingTime,locationRow,hero,activities,estimator,sevenDayCard,bars,places,historyView,profile,sourceNote}):`<header class="m-header"><a href="index.html" class="m-brand">${icon('wind')}<span>Airify Health</span></a><button class="m-mode live" data-m-action="data-mode">${mode==='live'?'Open-Meteo':mode==='loading'?t('กำลังโหลด','Loading'):t('เชื่อมต่อไม่ได้','Offline')}</button></header>${mode==='error'?`<div class="m-banner" role="status">${t('โหลดข้อมูล Open-Meteo ไม่สำเร็จ ไม่มีการใช้ตัวเลขสมมติ กรุณาลองใหม่','Open-Meteo could not be loaded. No substitute readings are shown. Please retry.')}<button data-m-source="live">${t('ลองใหม่','Retry')}</button></div>`:''}<main id="m-content">${tab==='today'?today():tab==='places'?places():tab==='history'?historyView():profile()}</main><nav class="m-bottom-nav" aria-label="${t('เมนูหลักมือถือ','Mobile navigation')}">${[['today','sun','วันนี้','Today'],['places','pin','พื้นที่','Places'],['history','chart','ประวัติ','History'],['profile','user','บัญชี','Account']].map(([id,ico,th,en])=>`<button data-m-tab="${id}" class="${tab===id?'active':''}" ${tab===id?'aria-current="page"':''}>${icon(ico)}<span>${t(th,en)}</span></button>`).join('')}</nav><dialog class="m-sheet" id="m-sheet"></dialog>`;
    if(useDesktop()){const focusNode=focusId?document.getElementById(focusId):focusTab?root.querySelector(`.d-nav [data-m-tab="${focusTab}"]`):focusMap?root.querySelector(`[data-d-map="${focusMap}"]`):null;if(focusNode){if(focusId==='d-search'){focusNode.value=searchValue;if(searchValue.trim().length>=2){document.getElementById('d-search-results').hidden=false;mobileSearch(searchValue,'d-search-results');}}focusNode.focus({preventScroll:true});}}
    if((tab==='places'||(useDesktop()&&tab==='today'))&&useMobile())initMobileMap();
    for(const chart of root.querySelectorAll('.m-chart-scroll'))chart.scrollLeft=chart.scrollWidth;
    alignChartAxes();
    if(scroll>0)window.scrollTo({top:scroll,behavior:'instant'});
  }
  function openSheet(title,body){const sheet=document.getElementById('m-sheet');sheet.setAttribute('aria-labelledby','m-sheet-title');sheet.innerHTML=`<button class="m-sheet-close" aria-label="${t('ปิด','Close')}" data-m-action="close-sheet">×</button><h2 id="m-sheet-title">${title}</h2>${body}`;sheet.showModal();}
  function closeSheet(){document.getElementById('m-sheet')?.close();}
  function openSearch(){openSheet(t('เลือกพื้นที่ในประเทศไทย','Choose a place in Thailand'),`<label for="m-search">${t('จังหวัด อำเภอ หรือสถานที่','Province, district or place')}</label><input type="search" id="m-search" placeholder="${t('ค้นหาพื้นที่…','Search places…')}" autocomplete="off"><div class="m-sheet-results" id="m-search-results">${CITIES.map((p,i)=>`<button data-m-city="${i}">${esc(p.name)}<small>${esc(p.sub)}</small></button>`).join('')}</div><p>${t('เมื่อใช้ข้อมูลภายนอก ระบบส่งชื่อพื้นที่ที่ค้นหาไปยัง Open-Meteo','External search sends your query to Open-Meteo.')}</p>`);}
  let searchTimer,searchAbort;
  async function mobileSearch(q,targetId='m-search-results'){
    const target=document.getElementById(targetId);if(!target)return;
    searchAbort?.abort();const ac=new AbortController();searchAbort=ac;
    const local=CITIES.filter(p=>p.name.includes(q));let matches=local,failed=false;
    if(q.trim().length>=2){
      target.innerHTML=`<p>${t('กำลังค้นหา…','Searching…')}</p>`;
      const timer=setTimeout(()=>ac.abort(),10000);
      try{
        const res=await getJSON(`https://geocoding-api.open-meteo.com/v1/search?name=${encodeURIComponent(q.trim())}&count=12&language=${prefs.lang}&countryCode=TH`,ac.signal);
        if(searchAbort!==ac||!target.isConnected)return;
        matches=[...local,...(res.results||[]).filter(p=>upToThailand(p.latitude,p.longitude)).map(p=>({name:p.name,sub:[p.admin2,p.admin1].filter(Boolean).join(', '),lat:p.latitude,lon:p.longitude}))];
      }catch(e){if(searchAbort!==ac||!target.isConnected)return;failed=true;}
      finally{clearTimeout(timer);}
    }
    if(searchAbort!==ac||!target.isConnected)return;
    const unique=matches.filter((p,i,arr)=>arr.findIndex(a=>Math.abs(a.lat-p.lat)<.01&&Math.abs(a.lon-p.lon)<.01)===i).slice(0,14);
    target.replaceChildren();
    for(const p of unique){const btn=document.createElement('button');btn.textContent=p.name;const small=document.createElement('small');small.textContent=p.sub;btn.append(small);btn.onclick=()=>selectPlace(p);target.append(btn);}
    if(failed){const note=document.createElement('p');note.textContent=t('ค้นหาภายนอกไม่สำเร็จ แสดงเฉพาะพื้นที่ที่มีในเครื่อง ลองพิมพ์ค้นหาอีกครั้ง','External search failed. Showing locally listed places only. Type again to retry.');target.append(note);}
    else if(!unique.length)target.innerHTML=`<p>${t('ไม่พบพื้นที่ ลองชื่อภาษาไทยหรืออังกฤษ','No results. Try a Thai or English place name.')}</p>`;
  }
  function selectPlace(p){closeSheet();cancelPinning();liveHistory=null;historyLoading=false;historyLoadError=false;mapViewport={lat:p.lat,lon:p.lon,zoom:13};if(mobileMap)mobileMap.setView([p.lat,p.lon],13,{animate:false});liveBusy=true;choosePlace(p).finally(()=>{liveBusy=false;render();if(tab==='history'||tab==='today')loadHistoricalReadings();});render();}
  async function useLive(){prefs.source='live';savePrefs();liveBusy=true;mode='loading';data=null;liveHistory=null;render();await loadLive();liveBusy=false;render();}
  async function loadHistoricalReadings(){
    const key=`${selected.lat},${selected.lon}`;
    if(liveHistory?.key===key){historyLoading=false;historyLoadError=false;return;}
    if(liveHistoryRequest?.key===key){historyLoading=true;render();return liveHistoryRequest.promise;}
    historyLoading=true;historyLoadError=false;render();
    const abort=new AbortController(),request={key,promise:null,abort};
    const timer=setTimeout(()=>abort.abort(),15000);
    liveHistoryRequest?.abort.abort();
    request.promise=(async()=>{
      try{
        const res=await getJSON(`https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${selected.lat}&longitude=${selected.lon}&hourly=pm2_5&timezone=Asia%2FBangkok&past_days=30&forecast_days=1`,abort.signal);
        if(`${selected.lat},${selected.lon}`!==key||liveHistoryRequest!==request)return;
        liveHistory={key,hourly:(res.hourly?.time||[]).map((time,i)=>({time,pm:res.hourly.pm2_5?.[i]})).filter(r=>r.pm!==null&&Number.isFinite(+r.pm))};historyLoadError=false;
      }catch(e){
        if(`${selected.lat},${selected.lon}`===key&&liveHistoryRequest===request){historyLoadError=true;toast(t('เรียกข้อมูลย้อนหลังไม่ได้ กรุณาลองใหม่','Could not load historical data. Please try again.'));}
      }finally{
        clearTimeout(timer);
        if(liveHistoryRequest===request){liveHistoryRequest=null;if(`${selected.lat},${selected.lon}`===key){historyLoading=false;if(tab==='history'||tab==='today')render();}}
      }
    })();
    liveHistoryRequest=request;
    return request.promise;
  }
  function loadSavedReadings(){
    if(!saved.length||savedRequest)return;
    const entries=saved.map(p=>({...p})), key=entries.map(p=>`${p.lat},${p.lon}`).join('|');
    if(savedReadings.key===key)return;
    savedRequest=key;
    const request=new AbortController(), timer=setTimeout(()=>request.abort(),15000);
    getJSON(`https://air-quality-api.open-meteo.com/v1/air-quality?latitude=${entries.map(p=>p.lat).join(',')}&longitude=${entries.map(p=>p.lon).join(',')}&current=pm2_5&timezone=Asia%2FBangkok`,request.signal).then(res=>{
      if(saved.map(p=>`${p.lat},${p.lon}`).join('|')!==key)return;
      const list=Array.isArray(res)?res:[res];
      savedReadings=new Map(entries.map((p,i)=>[`${p.lat},${p.lon}`,list[i]?.current?.pm2_5??null]));savedReadings.key=key;
      if(tab==='places'&&!pinning&&!document.getElementById('m-sheet')?.open)render();
    }).catch(()=>toast(t('ยังโหลดค่าของสถานที่บันทึกไม่ได้','Saved-place readings are unavailable.'))).finally(()=>{
      clearTimeout(timer);savedRequest=null;
      if(saved.map(p=>`${p.lat},${p.lon}`).join('|')!==key)loadSavedReadings();
    });
  }
  function initMobileMap(){
    const elm=document.getElementById('m-map');if(!elm)return;
    if(!window.L){mapRetry=setTimeout(()=>{if((tab==='places'||(useDesktop()&&tab==='today'))&&document.getElementById('m-map')){if(window.L)initMobileMap();else elm.innerHTML=`<div class="m-map-fallback">${t('แผนที่ยังโหลดไม่ได้<br>คุณยังเลือกพื้นที่จากช่องค้นหาด้านบนได้','Map unavailable.<br>You can still use the area search above.')}</div>`;}},4500);return;}
    elm.replaceChildren();draftMarker=null;
    const viewport=mapViewport||{lat:selected.lat,lon:selected.lon,zoom:12};
    mobileMap=L.map(elm,{zoomControl:true,scrollWheelZoom:false,attributionControl:true,zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false}).setView([viewport.lat,viewport.lon],viewport.zoom);
    const satellite=useDesktop()&&desktopMapStyle==='satellite';
    L.tileLayer(satellite?'https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}':'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:satellite?'Imagery © <a href="https://www.arcgis.com/home/item.html?id=10df2279f9684e4a9f6a7f08febac2a9">Esri, Vantor, Earthstar Geographics, GIS User Community</a>':'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',maxZoom:18}).addTo(mobileMap);
    mobileMap.zoomControl.setPosition('bottomright');
    const rows=mapRows;
    for(const p of rows){
      if(!Number.isFinite(p.pm))continue;
      const marker=L.marker([p.lat,p.lon],{bubblingMouseEvents:false,icon:L.divIcon({className:'m-map-point',html:esc(num(p.pm)),iconSize:[32,32],iconAnchor:[16,16]})}).addTo(mobileMap);
      marker.getElement().style.background=p.pm<=20?'#4ec34c':p.pm<=35?'#ffb300':p.pm<=50?'#ff7f13':'#f24a40';
      marker.bindTooltip(`${esc(p.name)} · ${num(p.pm)} µg/m³`,{direction:'top'});
      marker.on('click',e=>{if(e.originalEvent)L.DomEvent.stopPropagation(e.originalEvent);selectPlace({...p,sub:p.name});});
    }
    for(const p of saved){
      if(!Number.isFinite(+p.lat)||!Number.isFinite(+p.lon))continue;
      const label=t('หมุดที่บันทึก: ','Saved pin: ')+(prefs.lang==='en'?(p.en||p.name):p.name);
      const marker=L.marker([p.lat,p.lon],{bubblingMouseEvents:false,title:label,icon:L.divIcon({className:'m-saved-map-pin',html:icon('pin'),iconSize:[29,35],iconAnchor:[14,31]})}).addTo(mobileMap).setZIndexOffset(700);
      marker.getElement()?.setAttribute('aria-label',label);
      marker.bindTooltip(esc(p.name),{direction:'top',offset:[0,-22]});
      marker.on('click',e=>{if(e.originalEvent)L.DomEvent.stopPropagation(e.originalEvent);openSavedPlace(p.id);});
    }
    L.marker([selected.lat,selected.lon],{title:t('พื้นที่ที่เลือก','Selected area'),icon:L.divIcon({className:'m-map-user',html:'',iconSize:[17,17]})}).addTo(mobileMap).bindTooltip(esc(placeName()));
    mobileMap.on('moveend',()=>{if(mobileMap){const c=mobileMap.getCenter();mapViewport={lat:c.lat,lon:c.lng,zoom:mobileMap.getZoom()};}});
    mobileMap.on('click',e=>{if(!upToThailand(e.latlng.lat,e.latlng.lng))return toast(t('เลือกพื้นที่ในประเทศไทย','Select a place in Thailand.'));if(!pinning)startPinning();setPinDraft(e.latlng.lat,e.latlng.lng);});
    if(pinning&&pinDraft)setPinDraft(pinDraft.lat,pinDraft.lon);else updatePinEditor();
    loadSavedReadings();if(!mapRows.length)loadCityReadings().then(rows=>{mapRows=rows;if((tab==='places'||(useDesktop()&&tab==='today'))&&rows.length&&!pinning&&!document.getElementById('m-sheet')?.open)render();});
  }
  function saveEstimate(){if(!prefs.travel)return toast(t('เปิดบันทึกประวัติในแท็บบัญชีก่อน','Enable saved history in Account first.'));if(!data)return toast(t('รอข้อมูลค่าฝุ่นก่อนบันทึก','Wait for an air quality reading first.'));const act=document.getElementById('activity').value,a=ACTIVITIES.find(a=>a[0]===act),dt=new Date(),rows=storage.get('airify-preview-history',[]);rows.unshift({id:`mobile-${Date.now()}`,timestamp:dt.toISOString(),at:dt.toLocaleString('th-TH'),place:selected.name,activity:a[2],en:act,emoji:a[1],act,minutes:document.getElementById('duration').value,value:estimateMass(),mode});if(storage.set('airify-preview-history',rows.slice(0,100)))toast(t('บันทึกสถานการณ์ในเครื่องนี้แล้ว','Scenario saved on this device.'));}
  function managePlaces(){
    openSheet(t('จัดการหมุดที่บันทึก','Manage saved pins'),`<p>${t('เปลี่ยนชื่อหรือลบหมุดได้ โดยพิกัดที่บันทึกจะไม่เปลี่ยนตามชื่อ','Rename or delete a pin. Renaming does not change its coordinates.')}</p><div class="m-pin-management">${saved.map(p=>`<div class="m-manage-pin"><label>${esc(p.name)}<input type="text" maxlength="40" data-m-rename="${esc(p.id)}" value="${esc(p.name)}"><small>${coordinateText(p)}</small></label><button type="button" class="m-delete-pin" data-m-delete-place="${esc(p.id)}" aria-label="${t('ลบหมุด ','Delete pin ')}${esc(p.name)}">${icon('trash')}</button></div>`).join('')||`<p>${t('ยังไม่มีหมุดที่บันทึก','No saved pins yet.')}</p>`}</div><button class="m-primary" data-m-action="start-pin">${t('ปักหมุดสถานที่ใหม่ +','Pin a new place +')}</button><p>${t('หมุดเก็บเฉพาะในเบราว์เซอร์เครื่องนี้','Pins are stored in this browser only.')}</p>`);
  }

  function coordinateText(point){return `${Number(point.lat).toFixed(5)}, ${Number(point.lon).toFixed(5)}`;}
  function updatePinEditor(){
    const form=document.getElementById('m-pin-form');if(!form)return;
    form.hidden=!pinning;document.getElementById('m-map')?.classList.toggle('is-pinning',pinning);
    const output=document.getElementById('m-pin-coordinates'),button=document.getElementById('m-save-pin'),input=document.getElementById('m-pin-name');
    output.textContent=pinDraft?coordinateText(pinDraft):t('ยังไม่ได้เลือกพิกัด','No coordinates selected yet');button.disabled=!pinDraft;
    if(input.value!==pinName)input.value=pinName;
  }
  function startPinning(){
    if(useDesktop()&&tab==='today')navigate('places');
    closeSheet();if(saved.length>=8)return toast(t('บันทึกได้สูงสุด 8 หมุด ลบหมุดเดิมก่อนเพิ่มใหม่','You can save up to 8 pins. Delete one before adding another.'));
    if(!pinning){pinning=true;pinDraft=null;pinName='';}
    updatePinEditor();document.getElementById('m-map-section')?.scrollIntoView({behavior:'instant',block:'start'});
  }
  function setPinDraft(lat,lon){
    if(!upToThailand(lat,lon))return toast(t('เลือกพื้นที่ในประเทศไทย','Select a place in Thailand.'));
    pinDraft={lat:Number(lat),lon:Number(lon)};
    if(mobileMap&&window.L){
      if(draftMarker)draftMarker.setLatLng([lat,lon]);
      else{draftMarker=L.marker([lat,lon],{draggable:true,autoPan:true,title:t('ลากหมุดเพื่อปรับตำแหน่ง','Drag to adjust the pin'),bubblingMouseEvents:false,icon:L.divIcon({className:'m-saved-map-pin m-draft-map-pin',html:icon('pin'),iconSize:[33,39],iconAnchor:[16,35]})}).addTo(mobileMap).setZIndexOffset(2000);draftMarker.on('dragend',()=>{const p=draftMarker.getLatLng();if(upToThailand(p.lat,p.lng))setPinDraft(p.lat,p.lng);else{draftMarker.setLatLng([pinDraft.lat,pinDraft.lon]);toast(t('เลือกพื้นที่ในประเทศไทย','Select a place in Thailand.'));}});}
    }
    updatePinEditor();
  }
  function cancelPinning(){pinning=false;pinDraft=null;pinName='';if(draftMarker&&mobileMap)mobileMap.removeLayer(draftMarker);draftMarker=null;updatePinEditor();}
  function savePin(){
    if(!pinDraft||!upToThailand(pinDraft.lat,pinDraft.lon))return toast(t('เลือกจุดบนแผนที่ก่อนบันทึก','Select a point on the map first.'));
    const name=document.getElementById('m-pin-name').value.trim();
    if(!name){document.getElementById('m-pin-name').focus();return toast(t('กรอกชื่อสถานที่','Enter a place name.'));}
    if(saved.length>=8)return toast(t('บันทึกได้สูงสุด 8 หมุด','You can save up to 8 pins.'));
    if(saved.some(p=>Math.abs(p.lat-pinDraft.lat)<.00005&&Math.abs(p.lon-pinDraft.lon)<.00005))return toast(t('พิกัดนี้มีหมุดบันทึกอยู่แล้ว เลือกจุดอื่นหรือเปลี่ยนชื่อหมุดเดิม','This point is already saved. Choose another point or rename its existing pin.'));
    const pin={id:`pin-${Date.now()}`,name,en:name,icon:'pin',sub:coordinateText(pinDraft),lat:pinDraft.lat,lon:pinDraft.lon,example:false};
    const next=[...saved,pin];if(!storage.set('airify-mobile-places',next))return;
    saved=next;savedReadings=new Map();pinning=false;pinDraft=null;pinName='';render();toast(t('บันทึกหมุดตามพิกัดจริงแล้ว','Pin saved at its real coordinates.'));
  }
  function openSavedPlace(id){
    const p=saved.find(p=>p.id===id);if(!p)return;
    openSheet(esc(prefs.lang==='en'?(p.en||p.name):p.name),`<p>${p.example?t('หมุดเริ่มต้น · ','Starter pin · '):''}${esc(p.sub||'')}</p><p class="m-pin-detail-coordinates">${icon('pin')}${coordinateText(p)}</p><p>${t('หมุดนี้บันทึกตามพิกัดบนแผนที่ในเบราว์เซอร์เครื่องนี้','This pin stores a real map coordinate in this browser.')}</p><button class="m-primary" data-m-view-place="${esc(id)}">${t('ดูค่าฝุ่นจากข้อมูลภายนอก','Load external air quality data')}</button><p>${t('ปุ่มดูค่าฝุ่นจะส่งพิกัดหมุดนี้ไป Open-Meteo เพื่อเรียกข้อมูลแบบจำลอง','Loading air quality sends this pin’s coordinates to Open-Meteo for model estimates.')}</p><button class="m-delete-pin-detail" data-m-delete-place="${esc(id)}">${icon('trash')}${t('ลบหมุดนี้','Delete this pin')}</button>`);
  }
  function confirmDeletePlace(id){
    const p=saved.find(p=>p.id===id);if(!p)return;
    openSheet(t('ลบหมุดที่บันทึก?','Delete this saved pin?'),`<p>${t('ต้องการลบหมุด','Delete')} <b>${esc(p.name)}</b> ${t('ออกจากรายการและแผนที่บนเครื่องนี้หรือไม่','from your saved list and map on this device?')}</p><button class="m-delete-pin-detail" data-m-confirm-delete-place="${esc(id)}">${t('ยืนยันลบหมุด','Confirm delete pin')}</button><button class="m-primary" data-m-action="close-sheet">${t('เก็บหมุดไว้','Keep pin')}</button>`);
  }
  function deletePlace(id){
    const next=saved.filter(p=>p.id!==id);if(next.length===saved.length)return;
    if(!storage.set('airify-mobile-places',next))return;
    saved=next;savedReadings=new Map();closeSheet();render();toast(t('ลบหมุดจากรายการและแผนที่แล้ว','Pin removed from your saved list and map.'));
  }
  async function viewSavedPlace(id){
    const p=saved.find(p=>p.id===id);if(!p)return;closeSheet();prefs.source='live';savePrefs();liveHistory=null;
    selectPlace(p);
  }
  async function locate(){if(!navigator.geolocation)return toast(t('อุปกรณ์ไม่รองรับตำแหน่ง','Geolocation is unavailable.'));toast(t('กำลังขอตำแหน่งจากอุปกรณ์…','Requesting your location…'));navigator.geolocation.getCurrentPosition(p=>{prefs.location=true;savePrefs();if(!upToThailand(p.coords.latitude,p.coords.longitude))return toast(t('ตำแหน่งนี้อยู่นอกประเทศไทย','This location is outside Thailand.'));selectPlace({name:t('ตำแหน่งของฉัน','My location'),sub:t('ตำแหน่งโดยประมาณ','Approximate location'),lat:p.coords.latitude,lon:p.coords.longitude});},()=>{prefs.location=false;savePrefs();render();toast(t('เข้าถึงตำแหน่งไม่ได้ โปรดอนุญาตในเบราว์เซอร์หรือเลือกพื้นที่เอง','Location unavailable. Allow browser access or select a place manually.'));},{timeout:10000,enableHighAccuracy:false});}
  function navigate(id){closeSheet();if(tab!==id)cancelPinning();if(tab===id){window.scrollTo({top:0,behavior:'instant'});return;}if(id==='history'&&liveHistory?.key!==`${selected.lat},${selected.lon}`)historyLoading=true;view(id);window.scrollTo({top:0,behavior:'instant'});if(id==='history'||id==='today')loadHistoricalReadings();}
  const actions={
    'retry-history':()=>loadHistoricalReadings(),
    'desktop-share':async()=>{const url=new URL(location.href);url.searchParams.set('lat',selected.lat.toFixed(5));url.searchParams.set('lon',selected.lon.toFixed(5));url.searchParams.set('place',selected.name);try{await navigator.clipboard.writeText(url.href);toast(t('คัดลอกลิงก์พื้นที่แล้ว','Area link copied.'));}catch{openSheet(t('ลิงก์พื้นที่','Area link'),`<p>${t('คัดลอกลิงก์นี้เพื่อเปิดพื้นที่เดียวกัน','Copy this link to open the same area.')}</p><input readonly aria-label="${t('ลิงก์พื้นที่','Area link')}" value="${esc(url.href)}">`);}},
    'start-pin':startPinning,'cancel-pin':cancelPinning,'pin-center':()=>{if(!mobileMap)return toast(t('รอแผนที่โหลดก่อนเลือกพิกัด','Wait for the map to load first.'));const c=mobileMap.getCenter();setPinDraft(c.lat,c.lng);},
    search:openSearch,locate,history:()=>navigate('history'),
    activities:()=>{allActivities=!allActivities;render();},'all-records':()=>{allRecords=!allRecords;render();},
    'expand-map':()=>{expanded=!expanded;render();},'save-estimate':saveEstimate,'manage-places':managePlaces,
    'close-sheet':closeSheet,'data-mode':()=>navigate('profile'),
    'air-info':()=>openSheet(t('เกี่ยวกับข้อมูลคุณภาพอากาศ','About air quality data'),`<p>${t('ใช้ค่าฝุ่นและ AQI (US) จากแบบจำลอง Open-Meteo / CAMS ซึ่งเป็นค่าประมาณเชิงพื้นที่ ไม่ใช่ค่าจากเซนเซอร์ระดับถนน','Air readings and US AQI are spatial model estimates from Open-Meteo / CAMS, not street-level sensor measurements.')}</p><p>${readingTime()}</p><p>${t('ค่าปัจจุบันและกราฟย้อนหลังมาจาก Open-Meteo เท่านั้น ส่วนพยากรณ์ล่วงหน้าที่คำนวณเพิ่มใช้ป้าย Airify · ทดลอง ไม่ได้นำมาแทนค่าปัจจุบัน หากเชื่อมต่อไม่ได้จะแสดงว่าไม่มีข้อมูล','Current and historical readings come only from Open-Meteo. Extended forecasts carry an Airify · trial label and never replace current readings. Failed requests leave readings unavailable.')}</p>`),
    account:()=>navigate('profile'),
    'estimate-info':()=>openSheet(t('วิธีประเมินการรับฝุ่น','How exposure is estimated'),`<p>${t('ปริมาณฝุ่นที่อาจสูดเข้า = PM2.5 (µg/m³) × อัตราหายใจของกิจกรรม (m³/ชั่วโมง) × ระยะเวลา (ชั่วโมง) × ปัจจัยสภาพแวดล้อม × ปัจจัยหน้ากาก','Estimated inhaled mass = PM2.5 (µg/m³) × activity breathing rate (m³/hour) × time (hours) × environment factor × mask factor.')}</p><p>${t('หน้ามือถือเริ่มด้วยกลางแจ้งและไม่ใส่หน้ากาก การเทียบกับนั่งพักเป็นการเทียบอัตราการหายใจในเวลาเท่ากัน ไม่ใช่ระดับความเสี่ยงทางการแพทย์หรือปริมาณที่สะสมในปอด','Mobile defaults are outdoors with no mask. Comparison with rest uses breathing rates for the same duration. This does not measure medical risk or lung deposition.')}</p>`),
    'chart-details':()=>openSheet(t('ข้อมูล PM2.5 รายวัน','Daily PM2.5 values'),`<p>${t('ค่าเฉลี่ยจากข้อมูลรายชั่วโมงที่ผู้ให้บริการส่งกลับ','Averages from available hourly model data')}</p><div class="m-sheet-results">${dailyReadings().map(r=>`<div>${localeDate(r.time)} <b style="float:right">${num(r.pm,1)} µg/m³</b></div>`).join('')}</div>`),
    insights:()=>openSheet(t('คำแนะนำสำหรับการวางแผน','Plan your activities'),`<p>${t('เปรียบเทียบค่าฝุ่นก่อนออกเดินทาง ลองลดเวลาหรือความหนักของกิจกรรมกลางแจ้งเมื่อค่าฝุ่นสูง และติดตามประกาศจากหน่วยงานสาธารณสุข','Compare readings before travelling. Consider shorter or less intense outdoor activities during elevated pollution and follow public health advisories.')}</p><p>${t('ค่าประเมินในเว็บใช้เพื่อเปรียบเทียบสถานการณ์ ไม่สามารถระบุว่าปริมาณใดปลอดภัยสำหรับรายบุคคล','This estimator compares scenarios and does not define a safe personal exposure limit.')}</p>`),
    privacy:()=>openSheet(t('ความเป็นส่วนตัวของคุณ','Your privacy'),`<p>${t('ชื่อที่แสดง การตั้งค่า สถานที่บันทึก และประวัติที่กดบันทึกจะเก็บใน localStorage ของเบราว์เซอร์นี้เท่านั้น ไม่มีการส่งข้อมูลเหล่านี้ไปยังบัญชีผู้ใช้หรือเซิร์ฟเวอร์ Airify','Your display profile, settings, saved places and explicitly saved history stay in this browser’s localStorage. They are not sent to an Airify account or server.')}</p><p>${t('เมื่อเลือกข้อมูลภายนอก พิกัดพื้นที่จะถูกส่งไปยัง Open-Meteo ชื่อพื้นที่ที่ค้นหาถูกส่งไปยังบริการค้นหา และแผนที่โหลดภาพจาก OpenStreetMap ตัวเลือกการแบ่งปันข้อมูลเป็นการสาธิตเท่านั้น ไม่มีระบบวิเคราะห์พฤติกรรมส่งข้อมูลออก','External mode sends selected coordinates to Open-Meteo. Search sends place queries to its geocoding service, and map tiles load from OpenStreetMap. The sharing switch is a preference demonstration; no analytics are transmitted.')}</p>`),
    'edit-profile':()=>openSheet(t('แก้ไขบัญชีตัวอย่าง','Edit demo profile'),`<p>${t('ข้อมูลนี้อยู่ในเครื่องคุณ ไม่ใช่บัญชีออนไลน์','This is a local demo profile, not an online account.')}</p><form id="m-profile-form"><label>${t('ชื่อที่แสดง','Display name')}<input type="text" name="name" maxlength="40" value="${esc(prefs.name)}" required></label><button type="submit" class="m-primary">${t('บันทึกชื่อ','Save name')}</button></form>`),
    logout:()=>{if(prefs.guest){prefs.guest=false;savePrefs();render();return;}openSheet(t('ออกจากบัญชีตัวอย่าง?','Leave the demo profile?'),`<p>${t('คุณจะใช้งานต่อในชื่อผู้เยี่ยมชม ประวัติและการตั้งค่าในเครื่องยังอยู่','Continue as a guest. Your saved scenarios and local settings remain available.')}</p><button class="m-primary" data-m-action="confirm-logout">${t('ใช้งานแบบผู้เยี่ยมชม','Continue as guest')}</button>`);},
    'confirm-logout':()=>{prefs.guest=true;savePrefs();closeSheet();render();},
    'add-place':startPinning
  };
  root.addEventListener('click',event=>{const b=event.target.closest('button');if(!b)return;if(b.dataset.dMap){desktopMapStyle=b.dataset.dMap==='satellite'?'satellite':'street';render();return;}if(b.dataset.mDeletePlace)return confirmDeletePlace(b.dataset.mDeletePlace);if(b.dataset.mConfirmDeletePlace)return deletePlace(b.dataset.mConfirmDeletePlace);if(b.dataset.mViewPlace)return viewSavedPlace(b.dataset.mViewPlace);if(b.dataset.mDeleteRecord){const id=b.dataset.mDeleteRecord;openSheet(t('ลบสถานการณ์นี้?','Delete this scenario?'),`<p>${t('ลบเฉพาะสถานการณ์ที่คุณบันทึกในเบราว์เซอร์นี้','This deletes only this locally saved scenario.')}</p><button class="m-primary" data-m-delete-confirm="${esc(id)}">${t('ยืนยันการลบ','Confirm delete')}</button>`);return;}if(b.dataset.mDeleteConfirm){const id=b.dataset.mDeleteConfirm;storage.set('airify-preview-history',storage.get('airify-preview-history',[]).filter(r=>r.id!==id));closeSheet();render();toast(t('ลบสถานการณ์แล้ว','Scenario deleted.'));return;}if(b.dataset.mTab)return navigate(b.dataset.mTab);if(b.dataset.mSource==='live')return useLive();if(b.dataset.mCity!==undefined)return selectPlace({...CITIES[+b.dataset.mCity]});if(b.dataset.mPlace)return openSavedPlace(b.dataset.mPlace);if(b.dataset.mRecommendation!==undefined)return openRecommendation(Number(b.dataset.mRecommendation));if(b.dataset.mAct){applyRecommendationActivity(b.dataset.mAct);return;}if(b.dataset.mRange){historyDays=+b.dataset.mRange;render();if(liveHistory?.key!==`${selected.lat},${selected.lon}`)loadHistoricalReadings();return;}if(b.dataset.mRecord){const r=records().find(r=>(r.id||r.timestamp||r.at)===b.dataset.mRecord);if(r)openSheet(t('รายละเอียดกิจกรรม','Activity details'),`<p><b>${esc(r.activity)}</b><br>${esc(r.place)} · ${esc(r.minutes)} ${t('นาที','min')}<br>${esc(r.timestamp?new Date(r.timestamp).toLocaleString(prefs.lang==='en'?'en-GB':'th-TH'):r.at)}</p><p>${t('ปริมาณฝุ่นที่อาจสูดเข้า','Estimated inhaled mass')}: <b>${num(r.value,1)} µg</b></p><p>${t('สถานการณ์ที่ผู้ใช้กดบันทึกจากข้อมูลแบบจำลอง','An explicitly saved model scenario.')}</p>${String(r.id||'').startsWith('mobile-')?`<button class="m-primary" data-m-delete-record="${esc(r.id)}">${t('ลบสถานการณ์นี้','Delete this scenario')}</button>`:''}`);return;}actions[b.dataset.mAction]?.();});
  root.addEventListener('change',event=>{const el=event.target;if(el.id==='m-activity'||el.id==='m-duration'){const id=el.id==='m-activity'?'activity':'duration';document.getElementById(id).value=el.value;document.getElementById('environment').value=document.getElementById('activity').value==='indoor'?'indoor':'outdoor';updateEstimate();refreshEstimate();return;}if(el.id==='m-language'){prefs.lang=el.value;savePrefs();render();return;}if(el.id==='m-history-days'){historyDays=+el.value;render();if(liveHistory?.key!==`${selected.lat},${selected.lon}`)loadHistoricalReadings();return;}if(el.dataset.mRename){const p=saved.find(p=>p.id===el.dataset.mRename);if(p){const name=el.value.trim()||p.name;const next=saved.map(p=>p.id===el.dataset.mRename?{...p,name,en:name}:p);if(storage.set('airify-mobile-places',next)){saved=next;const row=[...root.querySelectorAll('[data-m-place]')].find(b=>b.dataset.mPlace===p.id)?.querySelector('.m-activity-copy b');if(row)row.textContent=name;for(const button of root.querySelectorAll('[data-m-delete-place]'))if(button.dataset.mDeletePlace===p.id)button.setAttribute('aria-label',t('ลบหมุด ','Delete pin ')+name);mobileMap?.eachLayer(layer=>{if(layer.options?.title===t('หมุดที่บันทึก: ','Saved pin: ')+p.name){layer.options.title=t('หมุดที่บันทึก: ','Saved pin: ')+name;layer.getElement()?.setAttribute('title',layer.options.title);layer.getElement()?.setAttribute('aria-label',layer.options.title);layer.setTooltipContent(esc(name));}});}}return;}if(el.dataset.mSetting){const key=el.dataset.mSetting;if(key==='location'&&el.checked){locate();return;}prefs[key]=el.checked;savePrefs();if(key==='dark'){root.dataset.theme=prefs.dark?'dark':'light';document.body.dataset.airifyTheme=prefs.dark?'dark':'light';return;}if(key==='location')toast(t('ปิดการใช้ตำแหน่งในแอปแล้ว สิทธิ์เบราว์เซอร์จัดการได้ในตั้งค่าเว็บไซต์','App location use disabled. Browser permissions are managed in site settings.'));if(key==='sharing')toast(t('บันทึกตัวเลือกแล้ว ไม่มีการส่งข้อมูลออกจากเครื่อง','Preference saved. No data is transmitted'));}});
  root.addEventListener('input',event=>{if(event.target.id==='m-pin-name')pinName=event.target.value;if(event.target.id==='d-search'){clearTimeout(searchTimer);const q=event.target.value,target=document.getElementById('d-search-results');target.hidden=q.trim().length<2;if(!target.hidden)searchTimer=setTimeout(()=>mobileSearch(q,'d-search-results'),300);return;}if(event.target.id==='m-search'){clearTimeout(searchTimer);const q=event.target.value;searchTimer=setTimeout(()=>mobileSearch(q),300);}});
  root.addEventListener('submit',event=>{if(event.target.id==='m-pin-form'){event.preventDefault();savePin();return;}if(event.target.id==='m-profile-form'){event.preventDefault();prefs.name=new FormData(event.target).get('name').trim()||prefs.name;savePrefs();closeSheet();render();toast(t('บันทึกชื่อในเครื่องแล้ว','Display name saved on this device.'));}});
  window.addEventListener('airify:data',()=>{if(initialized&&!pinning&&!document.getElementById('m-sheet')?.open)render();});
  window.addEventListener('hashchange',()=>{if(initialized){render();window.scrollTo({top:0,behavior:'instant'});}});
  const changeLayout=()=>{if(useMobile()&&!initialized)start();else render();};
  mq.addEventListener('change',changeLayout);desktopMq.addEventListener('change',changeLayout);
  function start(){initialized=true;if(useMobile()){document.getElementById('duration').step='5';document.getElementById('environment').value='outdoor';document.getElementById('mask').value='none';}savePrefs();render();if(useMobile()&&(tab==='history'||tab==='today'))loadHistoricalReadings();}
  start();
  const sharedArea=new URLSearchParams(location.search);
  if(sharedArea.has('lat')&&sharedArea.has('lon')){const lat=Number(sharedArea.get('lat')),lon=Number(sharedArea.get('lon'));if(Number.isFinite(lat)&&Number.isFinite(lon)&&upToThailand(lat,lon))selectPlace({name:(sharedArea.get('place')||t('พื้นที่ที่แชร์','Shared area')).slice(0,100),sub:t('พื้นที่จากลิงก์ที่แชร์','Area from a shared link'),lat,lon});}
  if(typeof ResizeObserver!=='undefined')new ResizeObserver(alignChartAxes).observe(root);
})();
