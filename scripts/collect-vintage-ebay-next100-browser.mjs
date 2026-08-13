#!/usr/bin/env node
import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT='docs/research/vintage-market-evidence';
const SEED=`${ROOT}/requests/next100-candidate-ids.txt`;
const TARGET=Number(process.env.VINTAGE_TARGET||15);
const BATCH_TAG=process.env.VINTAGE_BATCH_TAG||new Date().toISOString().replace(/[:.]/g,'-');
const OUT=`${ROOT}/batches/ebay-sold-checkpoint-${BATCH_TAG}.jsonl`;
const CONCURRENCY=Number(process.env.VINTAGE_CONCURRENCY||6);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function ingest(file, seen){try{for(const line of (await readFile(file,'utf8')).split(/\n+/)){if(!line.trim()) continue; const r=JSON.parse(line); if(r.listing_id) seen.add(String(r.listing_id));}}catch{}}
const seen=new Set();
for(const name of await readdir(ROOT)){if(name.endsWith('.jsonl')) await ingest(path.join(ROOT,name),seen);}
try{for(const name of await readdir(`${ROOT}/batches`)){if(name.endsWith('.jsonl')) await ingest(`${ROOT}/batches/${name}`,seen);}}catch{}
const candidateIds=[...new Set((await readFile(SEED,'utf8')).match(/\d{9,15}/g)||[])].filter(id=>!seen.has(id));
console.log(`SEED ${candidateIds.length} unseen candidates after dedupe against ${seen.size} existing IDs`);

function classify(title){
 const rules=[
 ['Stussy','streetwear'],['Vision Street Wear','skate'],['Vision','skate'],['Powell Peralta','skate'],['Santa Cruz','skate'],['Independent','skate'],['Thrasher','skate'],['Spitfire','skate'],['Airwalk','skate'],['Alien Workshop','skate'],['World Industries','skate'],['Blind','skate'],['Hook Ups','skate'],['Hook-Ups','skate'],['Fresh Jive','streetwear'],['FreshJive','streetwear'],['Gotcha','surf'],['Mambo','australian-surf-street'],['Quiksilver','surf'],['Quicksilver','surf'],['Billabong','surf'],['Rusty','surf'],['Rip Curl','surf'],['T&C','surf'],['Ocean Pacific','surf'],['Mossimo','streetwear'],['No Fear','streetwear'],['Volcom','skate-surf'],['Hobie','surf'],['Hurley','surf'],['Element','skate'],['Zero','skate'],['Toy Machine','skate'],['Plan B','skate'],["O'Neill",'surf'],['ONeill','surf'],['Globe','skate'],['Zoo York','streetwear-skate'],['Chocolate','skate'],['Girl Skateboards','skate'],['Creature','skate'],['Shorty','skate'],['Adio','skate'],['Vans','skate'],['Fallen','skate'],['Lost','surf'],['Famous Stars','streetwear-skate'],['Metal Mulisha','action-sports'],['Skin Industries','action-sports'],['Ecko','streetwear'],['Alva','skate']
 ];
 for(const [brand,tradition] of rules){if(title.toLowerCase().includes(brand.toLowerCase())) return {brand,tradition};}
 return {brand:'Other',tradition:'surf-skate-street'};
}
function eraOf(title){const t=title.toLowerCase(); if(/80s|198\d/.test(t)) return '80s'; if(/90s|199\d/.test(t)) return '90s'; if(/y2k|2000|00s/.test(t)) return 'Y2K'; return 'vintage';}

const browser=await chromium.launch({headless:true,args:['--disable-blink-features=AutomationControlled','--no-sandbox']});
const context=await browser.newContext({viewport:{width:1440,height:1200},locale:'en-AU',userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'});
const rows=[];
let cursor=0;
async function verify(id){
 const p=await context.newPage();
 try{
  await p.goto(`https://www.ebay.com/itm/${id}`,{waitUntil:'domcontentloaded',timeout:30000});
  await sleep(650);
  const body=(await p.locator('body').innerText({timeout:5000}).catch(()=>''))||'';
  if(/pardon our interruption|security measure|access denied|captcha/i.test(body)) return null;
  if(!/(This listing sold on|This item was sold|\bSOLD\b|Sold item|se vendi[oó])/i.test(body)) return null;
  const title=((await p.title().catch(()=>''))||'').replace(/\s*\|\s*eBay.*$/i,'').trim();
  if(!/shirt|t-?shirt|tee|hoodie|sweatshirt|cap|hat|jersey|crewneck|polo/i.test(title)) return null;
  const {brand,tradition}=classify(title);
  const soldDate=body.match(/(?:This listing sold on|This item was sold on)\s+([^\n.]+)/i)?.[1]?.trim()||null;
  const priceRaw=body.match(/(?:US |AU |C )?\$([0-9,]+(?:\.\d{2})?)/)?.[1];
  const imgs=await p.locator('img').evaluateAll(imgs=>imgs.map(i=>i.currentSrc||i.src).filter(u=>/ebayimg\.com\/images\/g\//i.test(u||''))).catch(()=>[]);
  return {id:`EBAY-SEED-${id}`,marketplace:'ebay',listing_id:id,sold:true,title,brand,tradition,era_claim:eraOf(title),sold_price:priceRaw?Number(priceRaw.replace(/,/g,'')):null,currency:/AU \$/.test(body)?'AUD':/C \$/.test(body)?'CAD':'USD',image_count:new Set(imgs).size||null,sold_date:soldDate,source_url:`https://www.ebay.com/itm/${id}`,retrieved:new Date().toISOString().slice(0,10),collector:'web-index-seeded-ebay-playwright-verified'};
 }catch{return null;} finally{await p.close();}
}
async function worker(){
 while(rows.length<TARGET){
  const i=cursor++; if(i>=candidateIds.length) return;
  const id=candidateIds[i];
  const row=await verify(id);
  if(row && rows.length<TARGET){rows.push(row); console.log(`${rows.length}/${TARGET} ${id} ${row.brand} ${row.era_claim}`);}
 }
}
await Promise.all(Array.from({length:CONCURRENCY},()=>worker()));
await browser.close();
if(rows.length!==TARGET) throw new Error(`Only collected ${rows.length}/${TARGET} unique verified sold listings from ${candidateIds.length} unseen seeded candidates`);
rows.sort((a,b)=>a.listing_id.localeCompare(b.listing_id));
await writeFile(OUT,rows.map(r=>JSON.stringify(r)).join('\n')+'\n');
console.log(JSON.stringify({added:rows.length,out:OUT,existing_before:seen.size,unseen_seed:candidateIds.length,batch_tag:BATCH_TAG},null,2));
