#!/usr/bin/env node
import { chromium } from 'playwright';
import { mkdir, readFile, readdir, writeFile, access } from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';

const AGENT=Number(process.env.VINTAGE_AGENT_ID||1), AGENT_COUNT=Number(process.env.VINTAGE_AGENT_COUNT||4), TARGET=Number(process.env.VINTAGE_TARGET||15);
const STATE=process.env.VINTAGE_AGENT_STATE, OUTBOX=process.env.VINTAGE_AGENT_OUTBOX, IMG=process.env.VINTAGE_IMAGE_ROOT, DOC=process.env.VINTAGE_EVIDENCE_DOC_ROOT;
if(!STATE||!OUTBOX||!IMG||!DOC) throw new Error('agent paths missing');
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const enabled=async()=>access(path.join(STATE,'enabled')).then(()=>true).catch(()=>false);
const state=async(v)=>writeFile(path.join(STATE,'state.json'),JSON.stringify({...v,updated_at:new Date().toISOString()},null,2));
const seen=new Set();
async function ingest(dir){try{for(const n of await readdir(dir)){if(n.endsWith('.jsonl')){for(const l of (await readFile(path.join(dir,n),'utf8')).split(/\n+/)){if(!l.trim())continue;try{const r=JSON.parse(l);if(r.listing_id)seen.add(String(r.listing_id));}catch{}}}}}catch{}}
await mkdir(STATE,{recursive:true}); await mkdir(OUTBOX,{recursive:true}); await mkdir(IMG,{recursive:true});
await ingest(DOC); await ingest(path.join(DOC,'batches')); await ingest(OUTBOX);
try{for(const n of await readdir(IMG)){if(/^\d{9,15}$/.test(n))seen.add(n)}}catch{}
const seedFile=path.join(DOC,'requests','next100-candidate-ids.txt');
let ids=[...new Set(((await readFile(seedFile,'utf8').catch(()=>'' )).match(/\d{9,15}/g)||[]))];
const shard=id=>Number(BigInt(id)%BigInt(AGENT_COUNT))===AGENT-1;
ids=ids.filter(id=>!seen.has(id)&&shard(id));
const browser=await chromium.launch({headless:true,args:['--disable-blink-features=AutomationControlled','--no-sandbox']});
const context=await browser.newContext({viewport:{width:1440,height:1200},locale:'en-AU',userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/151 Safari/537.36'});
let completed=0,batches=0;
function classify(t){for(const [b,k] of [['Stussy','streetwear'],['Powell Peralta','skate'],['Santa Cruz','skate'],['Thrasher','skate'],['Spitfire','skate'],['Independent','skate'],['Quiksilver','surf'],['Billabong','surf'],['Rip Curl','surf'],['Volcom','skate-surf'],['Creature','skate'],['Metal Mulisha','action-sports'],['Element','skate'],['Ecko','streetwear'],['RVCA','surf-skate'],['Girl','skate'],['Zero','skate'],['Anti Hero','skate'],['The Hundreds','streetwear'],['Obey','streetwear']])if(t.toLowerCase().includes(b.toLowerCase()))return{brand:b,tradition:k};return{brand:'Other',tradition:'surf-skate-street'}}
function era(t){t=t.toLowerCase();return /80s|198\d/.test(t)?'80s':/90s|199\d/.test(t)?'90s':/y2k|2000|00s/.test(t)?'Y2K':'vintage'}
async function verify(id){const p=await context.newPage();try{await p.goto(`https://www.ebay.com/itm/${id}`,{waitUntil:'domcontentloaded',timeout:30000});await sleep(650);const body=await p.locator('body').innerText({timeout:5000}).catch(()=>'');if(/pardon our interruption|security measure|access denied|captcha/i.test(body)||!/(This listing sold on|This item was sold|\bSOLD\b|Sold item)/i.test(body))return null;const title=((await p.title().catch(()=>''))||'').replace(/\s*\|\s*eBay.*$/i,'').trim();if(!/shirt|t-?shirt|tee|hoodie|sweatshirt|cap|hat|jersey|crewneck|polo/i.test(title))return null;const imgs=[...new Set(await p.locator('img').evaluateAll(xs=>xs.map(i=>i.currentSrc||i.src).filter(u=>/ebayimg\.com\/images\/g\//i.test(u||''))).catch(()=>[]))].slice(0,12);if(!imgs.length)return null;const d=path.join(IMG,id);await mkdir(d,{recursive:true});const prov=[];let n=0;for(const u0 of imgs){try{const u=u0.replace(/s-l\d+\.(jpg|jpeg|png|webp)$/i,'s-l1600.$1');const r=await context.request.get(u,{timeout:25000,headers:{referer:'https://www.ebay.com/'}});if(!r.ok())continue;const buf=await r.body();if(buf.length<3500)continue;n++;const file=`image-${String(n).padStart(2,'0')}.jpg`;await writeFile(path.join(d,file),buf);prov.push({file,source_url:u,source_kind:'ebay-rendered',sha256:crypto.createHash('sha256').update(buf).digest('hex'),byte_size:buf.length,acquired_at:new Date().toISOString()});}catch{}}if(!n)return null;const c=classify(title);const row={id:`EBAY-AGENT-${id}`,marketplace:'ebay',listing_id:id,sold:true,title,...c,era_claim:era(title),source_url:`https://www.ebay.com/itm/${id}`,retrieved:new Date().toISOString().slice(0,10),collector:`oracle-agent-${AGENT}`,stored_image_count:n};await writeFile(path.join(d,'record.json'),JSON.stringify(row,null,2));await writeFile(path.join(d,'provenance.json'),JSON.stringify(prov,null,2));return row;}catch{return null}finally{await p.close()}}
while(await enabled()){
  const rows=[];
  await state({status:'collecting',batch_progress:0,batch_target:TARGET,completed_batches:batches,completed_records:completed});
  for(const id of ids){if(!(await enabled())||rows.length>=TARGET)break;if(seen.has(id))continue;const row=await verify(id);seen.add(id);if(row){rows.push(row);await state({status:'collecting',batch_progress:rows.length,batch_target:TARGET,completed_batches:batches,completed_records:completed,last_listing_id:id});}}
  if(rows.length<TARGET){await state({status:'candidate-exhausted',batch_progress:rows.length,batch_target:TARGET,completed_batches:batches,completed_records:completed,last_error:`Only ${rows.length}/${TARGET} verified in this shard`});break;}
  const stamp=new Date().toISOString().replace(/[:.]/g,'-');const out=path.join(OUTBOX,`agent-${AGENT}-${stamp}.jsonl`);await writeFile(out,rows.map(r=>JSON.stringify(r)).join('\n')+'\n');completed+=rows.length;batches++;await state({status:'checkpoint-complete',batch_progress:TARGET,batch_target:TARGET,completed_batches:batches,completed_records:completed,last_listing_id:rows.at(-1).listing_id});
  await sleep(1000);
}
await browser.close();
await state({status:'stopped',batch_progress:0,batch_target:TARGET,completed_batches:batches,completed_records:completed});
