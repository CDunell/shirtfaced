#!/usr/bin/env node
import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { chromium } from 'playwright';

const ROOT='docs/research/vintage-market-evidence';
const OUT=`${ROOT}/batches/ebay-sold-next100-browser-2026-08-13.jsonl`;
const TARGET=100;
const brands=[
 ['Stussy','streetwear'],['Vision Street Wear','skate'],['Powell Peralta','skate'],['Santa Cruz','skate'],['Independent','skate'],['Thrasher','skate'],['Airwalk','skate'],['Alien Workshop','skate'],['World Industries','skate'],['Blind Skateboards','skate'],['Hook Ups','skate'],['Freshjive','streetwear'],['Gotcha','surf'],['Mambo','australian-surf-street'],['Quiksilver','surf'],['Billabong','surf'],['Rusty','surf'],['Rip Curl','surf'],['T&C Surf Designs','surf'],['Ocean Pacific','surf'],['Mossimo','streetwear'],['No Fear','streetwear'],['Volcom','skate'],['Hobie','surf'],['Hurley','surf'],['DC Shoes','skate'],['Element','skate'],['Etnies','skate'],['Zero Skateboards','skate'],['Toy Machine','skate'],['Plan B','skate'],['Independent Trucks','skate'],["O'Neill",'surf'],['SMP','skate'],['Vision','skate'],['H-Street','skate'],['Dogtown','skate'],['Sims','skate'],['G&S','skate'],['Roxy','surf'],['Katin','surf'],['Lost','surf'],['Globe','skate'],['Zoo York','streetwear-skate'],['Fuct','streetwear'],['XLarge','streetwear']
];
const eras=['80s','90s','2000s','Y2K'];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function ingest(file, seen){try{for(const line of (await readFile(file,'utf8')).split(/\n+/)){if(!line.trim()) continue; const r=JSON.parse(line); if(r.listing_id) seen.add(String(r.listing_id));}}catch{}}
const seen=new Set();
for(const name of await readdir(ROOT)){if(name.endsWith('.jsonl')) await ingest(path.join(ROOT,name),seen);}
try{for(const name of await readdir(`${ROOT}/batches`)){if(name.endsWith('.jsonl')) await ingest(`${ROOT}/batches/${name}`,seen);}}catch{}

const browser=await chromium.launch({headless:true,args:['--disable-blink-features=AutomationControlled','--no-sandbox']});
const context=await browser.newContext({viewport:{width:1440,height:1200},locale:'en-AU',userAgent:'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36'});
const page=await context.newPage();
const rows=[];

function candidateStrings(value){
 const out=new Set([String(value||'')]);
 for(let i=0;i<3;i++){
  for(const s of [...out]){try{out.add(decodeURIComponent(s));}catch{}}
 }
 for(const s of [...out]){
  try{
   const u=new URL(s);
   for(const key of ['q','url','u','r','redir','redirect']){const v=u.searchParams.get(key); if(v) out.add(v);}
  }catch{}
 }
 return [...out];
}
function idsFromValues(values){
 const ids=[];
 for(const value of values){
  for(const s of candidateStrings(value)){
   const m=s.match(/(?:https?:\/\/)?(?:www\.)?ebay\.com\/itm\/(?:[^/?#]+\/)?(\d{9,15})/i) || s.match(/ebay\.com%2Fitm%2F(?:[^%]+%2F)?(\d{9,15})/i);
   if(m) ids.push(m[1]);
  }
 }
 return [...new Set(ids)];
}

async function idsFromCurrentPage(){
 const hrefs=await page.locator('a').evaluateAll(as=>as.map(a=>a.getAttribute('href')||a.href)).catch(()=>[]);
 const html=await page.content().catch(()=> '');
 const htmlMatches=[...html.matchAll(/(?:https?:\\?\/\\?\/)?(?:www\\?\.)?ebay\\?\.com\\?\/itm\\?\/(?:[^\"'<>?]+\\?\/)?(\d{9,15})/gi)].map(m=>m[1]);
 return [...new Set([...idsFromValues(hrefs),...htmlMatches])];
}

async function searchIds(brand,era,pageno){
 const start=(pageno-1)*10;
 const query=`site:ebay.com/itm \"This listing sold on\" vintage ${brand} ${era} (shirt OR tee OR hoodie OR cap)`;
 const google=`https://www.google.com/search?q=${encodeURIComponent(query)}&num=10&start=${start}&filter=0`;
 await page.goto(google,{waitUntil:'domcontentloaded',timeout:30000}).catch(()=>null);
 await sleep(700);
 let ids=await idsFromCurrentPage();
 if(ids.length) return ids;
 const bing=`https://www.bing.com/search?q=${encodeURIComponent(query)}&count=10&first=${start+1}`;
 await page.goto(bing,{waitUntil:'domcontentloaded',timeout:30000}).catch(()=>null);
 await sleep(700);
 return idsFromCurrentPage();
}

async function verify(id,brand,tradition,era){
 const p=await context.newPage();
 try{
  await p.goto(`https://www.ebay.com/itm/${id}`,{waitUntil:'domcontentloaded',timeout:30000});
  await sleep(700);
  const body=(await p.locator('body').innerText({timeout:5000}).catch(()=>''))||'';
  if(/pardon our interruption|security measure|access denied|captcha/i.test(body)) return null;
  if(!/(This listing sold on|This item was sold|\bSOLD\b|Sold item)/i.test(body)) return null;
  const title=((await p.title().catch(()=>''))||'').replace(/\s*\|\s*eBay.*$/i,'').trim();
  if(!/shirt|t-?shirt|tee|hoodie|sweatshirt|cap|hat|jersey|crewneck/i.test(title)) return null;
  const soldDate=body.match(/(?:This listing sold on|This item was sold on)\s+([^\n.]+)/i)?.[1]?.trim()||null;
  const priceRaw=body.match(/(?:US |AU |C )?\$([0-9,]+(?:\.\d{2})?)/)?.[1];
  const imgs=await p.locator('img').evaluateAll(imgs=>imgs.map(i=>i.currentSrc||i.src).filter(u=>/ebayimg\.com\/images\/g\//i.test(u||''))).catch(()=>[]);
  return {id:`EBAY-BROWSER-${id}`,marketplace:'ebay',listing_id:id,sold:true,title,brand,tradition,era_claim:era,sold_price:priceRaw?Number(priceRaw.replace(/,/g,'')):null,currency:/AU \$/.test(body)?'AUD':/C \$/.test(body)?'CAD':'USD',image_count:new Set(imgs).size||null,sold_date:soldDate,source_url:`https://www.ebay.com/itm/${id}`,retrieved:new Date().toISOString().slice(0,10),collector:'indexed-search-plus-ebay-playwright-verified'};
 }catch{return null;} finally{await p.close();}
}

for(const [brand,tradition] of brands){
 for(const era of eras){
  for(let pg=1;pg<=10 && rows.length<TARGET;pg++){
   const ids=await searchIds(brand,era,pg);
   console.log(`DISCOVERY ${brand} ${era} p${pg}: ${ids.length}`);
   for(const id of ids){
    if(rows.length>=TARGET) break;
    if(seen.has(id)) continue;
    const row=await verify(id,brand,tradition,era);
    if(!row) continue;
    rows.push(row); seen.add(id);
    console.log(`${rows.length}/${TARGET} ${id} ${brand} ${era}`);
   }
  }
  if(rows.length>=TARGET) break;
 }
 if(rows.length>=TARGET) break;
}
await browser.close();
if(rows.length!==TARGET) throw new Error(`Only collected ${rows.length}/${TARGET} unique verified sold listings`);
await writeFile(OUT,rows.map(r=>JSON.stringify(r)).join('\n')+'\n');
console.log(JSON.stringify({added:rows.length,out:OUT,total_seen:seen.size},null,2));
