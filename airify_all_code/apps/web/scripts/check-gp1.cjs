// Dependency-free checks for the static assignment pages and error recovery.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const base = path.resolve(__dirname, '../public/gp1');
const read = file => fs.readFileSync(path.join(base, file), 'utf8');
let passed = 0;
const pass = label => { passed++; console.log('PASS ' + label); };
const pages = ['index.html', 'about.html', 'try.html'];
for (const page of pages) {
  const html = read(page);
  const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(ids.length, new Set(ids).size, page + ': duplicate IDs');
  for (const [, raw] of html.matchAll(/(?:src|href)="([^"]+)"/g)) {
    if (/^(?:[a-z]+:|\/\/)/i.test(raw)) continue;
    const [resource, hash] = raw.split('#');
    const target = decodeURIComponent(resource.split('?')[0]) || page;
    assert.ok(fs.existsSync(path.join(base, target)), `${page}: missing ${raw}`);
    if (hash && target.endsWith('.html')) {
      const virtualTab = target === 'try.html' && ['today','places','history','profile'].includes(hash);
      assert.ok(virtualTab || read(target).includes(`id="${hash}"`), `${page}: missing anchor ${raw}`);
    }
  }
  pass(page + ': local assets, routes, anchors and unique IDs');
}
for (const file of fs.readdirSync(path.join(base, 'assets')).filter(x => x.endsWith('.css'))) {
  for (const [, ref] of read('assets/' + file).matchAll(/url\(["']?([^\s)'";]+)["']?\)/g)) {
    if (/^(?:[a-z]+:|\/\/|#)/i.test(ref)) continue;
    assert.ok(fs.existsSync(path.resolve(base, 'assets', ref.split(/[?#]/)[0])), `${file}: missing ${ref}`);
  }
}
pass('CSS referenced assets exist');
const team = vm.runInNewContext(read('assets/team.js') + ';TEAM', {document:{getElementById:()=>null}});
assert.equal(team.length, 4);
assert.equal(team.find(p=>p.initials==='TS').profile, 'https://jamethaksin.github.io/resume');
assert.ok(team.every(p=>p.profile.startsWith('https://') && fs.existsSync(path.join(base, p.photo))));
pass('four members have supplied resume URLs and photos');
const mobile = read('assets/mobile.js');
function extract(start, end) { return mobile.slice(mobile.indexOf(start), mobile.indexOf(end, mobile.indexOf(start))); }
class Node {
  constructor() { this.children=[]; this.isConnected=true; this.textContent=''; this.html=''; this.attrs={}; }
  set innerHTML(value) { this.html=value; this.children=[]; }
  get innerHTML() { return this.html; }
  replaceChildren() { this.html=''; this.children=[]; }
  append(...nodes) { this.children.push(...nodes); }
  setAttribute(k,v) { this.attrs[k]=v; }
  showModal() { this.open=true; }
}
async function main() {
  const target=new Node(), timers=[], cities=[{name:'กรุงเทพมหานคร',sub:'กรุงเทพมหานคร',lat:13.75,lon:100.5}];
  const context={document:{getElementById:()=>target,createElement:()=>new Node()},CITIES:cities,prefs:{lang:'th'},
    t:th=>th,AbortController,setTimeout:fn=>(timers.push(fn),timers.length),clearTimeout(){},
    getJSON:(_,signal)=>new Promise((resolve,reject)=>signal.addEventListener('abort',()=>reject(Error('Aborted')))),
    upToThailand:()=>true,selectPlace(){},searchAbort:null};
  vm.createContext(context);
  vm.runInContext(extract('  async function mobileSearch(', '  function selectPlace('),context);
  const pending=context.mobileSearch('กรุงเทพ'); timers.shift()(); await pending;
  assert.equal(target.children[0].textContent,'กรุงเทพมหานคร');
  assert.match(target.children.at(-1).textContent,/ค้นหาภายนอกไม่สำเร็จ/);
  assert.ok(!target.innerHTML.includes('กำลังค้นหา'));
  pass('search timeout exits loading and preserves local results');
  const noResults=context.mobileSearch('unknown-place'); timers.shift()(); await noResults;
  assert.match(target.children[0].textContent,/ลองพิมพ์ค้นหาอีกครั้ง/);
  pass('search failure with no local match explains retry');
  const old=context.mobileSearch('unknown-place');
  context.getJSON=async()=>({results:[]});
  await context.mobileSearch('กรุงเทพ'); await old;
  assert.equal(target.children[0].textContent,'กรุงเทพมหานคร');
  assert.equal(target.children.length,1);
  pass('cancelled older search cannot overwrite a newer result');
  const messages=[]; let writeOK=false;
  const saveContext={prefs:{travel:true},data:{pm:25},document:{getElementById:id=>({value:id==='activity'?'walking':'30'})},
    ACTIVITIES:[['walking','walk','เดินกลางแจ้ง']],Date,selected:{name:'กรุงเทพมหานคร'},mode:'live',
    storage:{get:()=>[],set:()=>writeOK},estimateMass:()=>15,toast:message=>messages.push(message),t:th=>th};
  vm.createContext(saveContext);
  vm.runInContext(extract('  function saveEstimate(', '  function managePlaces('),saveContext);
  saveContext.saveEstimate(); assert.equal(messages.length,0,'failed storage must not announce success');
  writeOK=true;saveContext.saveEstimate();assert.equal(messages.length,1);
  pass('save only announces success after storage accepts the record');
  const dialog=new Node();const modalContext={document:{getElementById:()=>dialog},t:th=>th};
  vm.createContext(modalContext);vm.runInContext(extract('  function openSheet(', '  function closeSheet('),modalContext);
  modalContext.openSheet('Test explanation','<p>Details</p>');
  assert.equal(dialog.attrs['aria-labelledby'],'m-sheet-title');
  assert.ok(dialog.innerHTML.includes('id="m-sheet-title"'));assert.ok(dialog.open);
  pass('explanation dialogs expose an accessible title');
  console.log(`${passed} GP1 checks passed.`);
}
main().catch(error=>{console.error(error);process.exitCode=1;});
