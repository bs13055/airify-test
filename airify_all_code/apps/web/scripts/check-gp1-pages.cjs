const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const dist=path.resolve(__dirname,'../dist');
const redirect=fs.readFileSync(path.join(dist,'index.html'),'utf8');
const worker=fs.readFileSync(path.join(dist,'service-worker.js'),'utf8');
const script=redirect.match(/<script>([\s\S]*?)<\/script>/)[1];
for(const route of ['https://bs13055.github.io/Airify/','https://bs13055.github.io/Airify/index.html','https://bs13055.github.io/Airify/#/developers']){
  let destination;
  vm.runInNewContext(script,{URL,location:{href:route,replace:value=>destination=value}});
  assert.equal(destination,'https://bs13055.github.io/Airify/gp1/');
}
assert.ok(fs.readFileSync(path.join(dist,'platform.html'),'utf8').includes('<div id="root"></div>'));
console.log('PASS root, index.html and old hash bookmarks open GP1; previous app retained');
async function main(){
  const handlers={},deleted=[],navigations=[];let claimed=false;
  vm.runInNewContext(worker,{URL,Promise,self:{registration:{scope:'https://bs13055.github.io/Airify/'},skipWaiting(){},
    addEventListener:(name,fn)=>handlers[name]=fn,
    clients:{claim:async()=>{claimed=true},matchAll:async()=>[
      {url:'https://bs13055.github.io/Airify/#/developers',navigate:async url=>navigations.push(url)},
      {url:'https://bs13055.github.io/resume/',navigate:async()=>{throw Error('Unrelated site must remain untouched')}},
      {url:'https://bs13055.github.io/Airify/gp1/try.html',navigate:async()=>{throw Error('Current GP1 page must remain untouched')}}
    ]}},caches:{keys:async()=>['airify-v1-static','other-site-cache'],delete:async key=>deleted.push(key)}});
  let activation;handlers.activate({waitUntil:promise=>activation=promise});await activation;
  assert.deepEqual(deleted,['airify-v1-static']);assert.ok(claimed);
  assert.deepEqual(navigations,['https://bs13055.github.io/Airify/gp1/']);assert.equal(handlers.fetch,undefined);
  console.log('PASS stale Airify cache migration preserves unrelated caches, pages and normal network requests');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
