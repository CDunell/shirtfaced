#!/usr/bin/env node
import { chromium } from 'playwright';
import { appendFile, mkdir, readFile, readdir, unlink, writeFile, access } from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const AGENT=Number(process.env.VINTAGE_AGENT_ID||1), AGENT_COUNT=Number(process.env.VINTAGE_AGENT_COUNT||4), TARGET=Number(process.env.VINTAGE_TARGET||15);
const STATE=process.env.VINTAGE_AGENT_STATE, OUTBOX=process.env.VINTAGE_AGENT_OUTBOX, IMG=process.env.VINTAGE_IMAGE_ROOT, DOC=process.env.VINTAGE_EVIDENCE_DOC_ROOT;
if(!STATE||!OUTBOX||!IMG||!DOC) throw new Error('agent paths missing');
// v2 deliberately retries candidates poisoned by the original deploy race,
// where Playwright disappeared after an ID had already been marked attempted.
const ENABLED=path.join(STATE,'enabled'), ATTEMPTED=path.join(STATE,'attempted-ids-v2.txt'), DISCOVERED=path.join(STATE,'discovered-ids.txt'), CURSOR=path.join(STATE,'discovery-cursor-v2.txt'), BUFFER=path.join(STATE,'checkpoint-buffer.jsonl');
const brands=['Stussy','Vision Street Wear','Powell Peralta','Santa Cruz','Independent Trucks','Thrasher','Airwalk','Alien Workshop','World Industries','Blind Skateboards','Hook Ups','Freshjive','Gotcha','Mambo','Quiksilver','Billabong','Rusty','Rip Curl','T&C Surf Designs','Ocean Pacific','Mossimo','No Fear','Volcom','Hobie','Hurley','DC Shoes','Element','Etnies','Zero Skateboards','Toy Machine','Girl Skateboards','Creature','RVCA'];
const eras=['80s','90s','2000s','Y2K'];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const enabled=async()=>access(ENABLED).then(()=>true).catch(()=>false);
const state=async v=>writeFile(path.join(STATE,'state.json'),JSON.stringify({...v,updated_at:new Date().toISOString()},null,2));
const lines=async file=>[...new Set(((await readFile(file,'utf8').catch(()=>'' )).match(/\d{9,15}/g)||[]))];
const rowsFrom=async file=>{const out=[];for(const line of (await readFile(file,'utf8').catch(()=>'')).split(/\n+/)){if(!line.trim())continue;try{out.push(JSON.parse(line))}catch{}}return out};
const saveRows=(file,rows)=>writeFile(file,rows.map(r=>JSON.stringify(r)).join('\n')+(rows.length?'\n':''));
const shard=id=>Number(BigInt(id)%BigInt(AGENT_COUNT))===AGENT-1;

await mkdir(STATE,{recursive:true}); await mkdir(OUTBOX,{recursive:true}); await mkdir(IMG,{recursive:true});
const seen=new Set(), attempted=new Set(await lines(ATTEMPTED)), discovered=new Set(await lines(DISCOVERED));
async function ingest(dir){try{for(const n of await readdir(dir)){if(n.endsWith('.jsonl')){for(const l of (await readFile(path.join(dir,n),'utf8')).split(/\n+/)){if(!l.trim())continue;try{const r=JSON.parse(l);if(r.listing_id)seen.add(String(r.listing_id));}catch{}}}}}catch{}}
await ingest(DOC); await ingest(path.join(DOC,'batches')); await ingest(OUTBOX);
let buffer=await rowsFrom(BUFFER);
const bufferedIds=new Set(buffer.map(r=>String(r.listing_id)));
try{for(const n of await readdir(IMG)){if(/^\d{9,15}$/.test(n)&&!bufferedIds.has(n))seen.add(n)}}catch{}
const seedFile=path.join(DOC,'requests','next100-candidate-ids.txt');
const seedIds=await lines(seedFile);
let discoveryCursor=Number((await readFile(CURSOR,'utf8').catch(()=>'0')).trim())||0;

const browser=await chromium.launch({headless:true,args:['--disable-blink-features=AutomationControlled','--no-sandbox']});
const context=await browser.newContext({viewport:{width:1440,height:1200},locale:'en-AU',userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36'});
let completed=0,batches=0,finalStatus='stopped',lastListing=null;

function classify(t){for(const [b,k] of [['Stussy','streetwear'],['Powell Peralta','skate'],['Santa Cruz','skate'],['Thrasher','skate'],['Spitfire','skate'],['Independent','skate'],['Quiksilver','surf'],['Billabong','surf'],['Rip Curl','surf'],['Volcom','skate-surf'],['Creature','skate'],['Metal Mulisha','action-sports'],['Element','skate'],['Ecko','streetwear'],['RVCA','surf-skate'],['Girl','skate'],['Zero','skate'],['Anti Hero','skate'],['The Hundreds','streetwear'],['Obey','streetwear']])if(t.toLowerCase().includes(b.toLowerCase()))return{brand:b,tradition:k};return{brand:'Other',tradition:'surf-skate-street'}}
function era(t){t=t.toLowerCase();return /80s|198\d/.test(t)?'80s':/90s|199\d/.test(t)?'90s':/y2k|2000|00s/.test(t)?'Y2K':'vintage'}

async function discover(minimum=60){
  const added=[];
  await state({status:'replenishing-candidates',batch_progress:buffer.length,batch_target:TARGET,completed_batches:batches,completed_records:completed,last_listing_id:lastListing,last_error:null});
  for(let scanned=0;scanned<16&&added.length<minimum&&await enabled();scanned++,discoveryCursor++){
    const queryIndex=Math.floor(discoveryCursor/8),page=discoveryCursor%8+1;
    if(queryIndex>=brands.length*eras.length)break;
    const brand=brands[Math.floor(queryIndex/eras.length)],eraName=eras[queryIndex%eras.length];
    const p=await context.newPage();
    try{
      const q=encodeURIComponent(`vintage ${brand} ${eraName} shirt t-shirt`);
      await p.goto(`https://www.ebay.com/sch/i.html?_nkw=${q}&LH_Sold=1&LH_Complete=1&_pgn=${page}&_ipg=120`,{waitUntil:'domcontentloaded',timeout:30000});
      await sleep(800);
      const hrefs=await p.locator('a[href*="/itm/"]').evaluateAll(as=>as.map(a=>a.href)).catch(()=>[]);
      for(const href of hrefs){const id=href.match(/\/itm\/(?:[^/?#]+\/)?(\d{9,15})/)?.[1];if(id&&shard(id)&&!seen.has(id)&&!attempted.has(id)&&!discovered.has(id)){discovered.add(id);added.push(id)}}
    }catch{}finally{await p.close()}
    await writeFile(CURSOR,String(discoveryCursor+1));
  }
  if(added.length)await appendFile(DISCOVERED,added.join('\n')+'\n');
  return added.length;
}

async function verify(id){const p=await context.newPage();try{await p.goto(`https://www.ebay.com/itm/${id}`,{waitUntil:'domcontentloaded',timeout:30000});await sleep(650);const body=await p.locator('body').innerText({timeout:5000}).catch(()=>'');if(/pardon our interruption|security measure|access denied|captcha/i.test(body)||!/(This listing sold on|This item was sold|\bSOLD\b|Sold item)/i.test(body))return null;const title=((await p.title().catch(()=>''))||'').replace(/\s*\|\s*eBay.*$/i,'').trim();if(!/shirt|t-?shirt|tee|hoodie|sweatshirt|cap|hat|jersey|crewneck|polo/i.test(title))return null;const imgs=[...new Set(await p.locator('img').evaluateAll(xs=>xs.map(i=>i.currentSrc||i.src).filter(u=>/ebayimg\.com\/images\/g\//i.test(u||''))).catch(()=>[]))].slice(0,12);if(!imgs.length)return null;const d=path.join(IMG,id);await mkdir(d,{recursive:true});const prov=[];let n=0;for(const u0 of imgs){try{const u=u0.replace(/s-l\d+\.(jpg|jpeg|png|webp)$/i,'s-l1600.$1');const r=await context.request.get(u,{timeout:25000,headers:{referer:'https://www.ebay.com/'}});if(!r.ok())continue;const buf=await r.body();if(buf.length<3500)continue;n++;const file=`image-${String(n).padStart(2,'0')}.jpg`;await writeFile(path.join(d,file),buf);prov.push({file,source_url:u,source_kind:'ebay-rendered',sha256:crypto.createHash('sha256').update(buf).digest('hex'),byte_size:buf.length,acquired_at:new Date().toISOString()});}catch{}}if(!n)return null;const c=classify(title);const row={id:`EBAY-AGENT-${id}`,marketplace:'ebay',listing_id:id,sold:true,title,...c,era_claim:era(title),source_url:`https://www.ebay.com/itm/${id}`,retrieved:new Date().toISOString().slice(0,10),collector:`oracle-agent-${AGENT}`,stored_image_count:n};await writeFile(path.join(d,'record.json'),JSON.stringify(row,null,2));await writeFile(path.join(d,'provenance.json'),JSON.stringify(prov,null,2));return row}catch{return null}finally{await p.close()}}

while(await enabled()){
  await state({status:'collecting',batch_progress:buffer.length,batch_target:TARGET,completed_batches:batches,completed_records:completed,last_listing_id:lastListing,last_error:null});
  let candidates=[...new Set([...seedIds,...discovered])].filter(id=>shard(id)&&!seen.has(id)&&!attempted.has(id)&&!bufferedIds.has(id));
  if(!candidates.length){const added=await discover();if(!(await enabled()))break;if(!added){finalStatus='candidate-exhausted';await unlink(ENABLED).catch(()=>{});break}candidates=[...discovered].filter(id=>!seen.has(id)&&!attempted.has(id)&&!bufferedIds.has(id))}
  for(const id of candidates){
    if(!(await enabled())||buffer.length>=TARGET)break;
    attempted.add(id);await appendFile(ATTEMPTED,id+'\n');
    const row=await verify(id);
    if(row){buffer.push(row);bufferedIds.add(id);lastListing=id;await saveRows(BUFFER,buffer);await state({status:'collecting',batch_progress:buffer.length,batch_target:TARGET,completed_batches:batches,completed_records:completed,last_listing_id:id,last_error:null})}
  }
  if(buffer.length<TARGET)continue;
  const batch=buffer.splice(0,TARGET),stamp=new Date().toISOString().replace(/[:.]/g,'-'),out=path.join(OUTBOX,`agent-${AGENT}-${stamp}.jsonl`);
  await saveRows(out,batch);await saveRows(BUFFER,buffer);completed+=batch.length;batches++;lastListing=batch.at(-1).listing_id;
  await state({status:'checkpoint-complete',batch_progress:TARGET,batch_target:TARGET,completed_batches:batches,completed_records:completed,last_listing_id:lastListing,last_error:null});
  await sleep(1000);
}
await browser.close();
if(finalStatus==='candidate-exhausted')await state({status:'candidate-exhausted',batch_progress:buffer.length,batch_target:TARGET,completed_batches:batches,completed_records:completed,last_listing_id:lastListing,last_error:'No unseen sold-listing candidates remain after automatic discovery'});
else await state({status:'stopped',batch_progress:buffer.length,batch_target:TARGET,completed_batches:batches,completed_records:completed,last_listing_id:lastListing,last_error:null});
