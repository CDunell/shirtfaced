#!/usr/bin/env node
import { readFile, readdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const ROOT='docs/research/vintage-market-evidence';
const OUT=`${ROOT}/batches/ebay-sold-next100-2026-08-13.jsonl`;
const TARGET=100;
const ua={'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36'};
const brands=[
 ['Stussy','streetwear'],['Vision Street Wear','skate'],['Powell Peralta','skate'],['Santa Cruz','skate'],['Independent','skate'],['Thrasher','skate'],['Airwalk','skate'],['Alien Workshop','skate'],['World Industries','skate'],['Blind Skateboards','skate'],['Hook Ups','skate'],['Freshjive','streetwear'],['Gotcha','surf'],['Mambo','australian-surf-street'],['Quiksilver','surf'],['Billabong','surf'],['Rusty','surf'],['Rip Curl','surf'],['T&C Surf Designs','surf'],['Ocean Pacific','surf'],['Mossimo','streetwear'],['No Fear','streetwear'],['Volcom','skate'],['Hobie','surf'],['Hurley','surf'],['DC Shoes','skate'],['Element','skate'],['Etnies','skate'],['Zero Skateboards','skate'],['Toy Machine','skate'],['Plan B','skate'],['Independent Trucks','skate'],['O Neill','surf'],['SMP','skate'],['Vision','skate']
];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const decode=s=>(s||'').replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;/g,"'");
const txt=h=>decode(h.replace(/<script[\s\S]*?<\/script>/gi,' ').replace(/<style[\s\S]*?<\/style>/gi,' ').replace(/<[^>]+>/g,' ').replace(/\s+/g,' '));

const seen=new Set();
async function ingest(file){try{for(const line of (await readFile(file,'utf8')).split(/\n+/)){if(!line.trim()) continue; const r=JSON.parse(line); if(r.listing_id) seen.add(String(r.listing_id));}}catch{}}
for(const name of await readdir(ROOT)){if(name.endsWith('.jsonl')) await ingest(path.join(ROOT,name));}
try{for(const name of await readdir(`${ROOT}/batches`)){if(name.endsWith('.jsonl')) await ingest(`${ROOT}/batches/${name}`);}}catch{}

const rows=[];
for(const [brand,tradition] of brands){
 for(const era of ['80s','90s','2000s','Y2K']){
  for(let page=1;page<=10 && rows.length<TARGET;page++){
   const q=encodeURIComponent(`vintage ${brand} ${era} shirt t-shirt hoodie cap`);
   const url=`https://www.ebay.com/sch/i.html?_nkw=${q}&LH_Sold=1&LH_Complete=1&_pgn=${page}&_ipg=120`;
   let html=''; try{const r=await fetch(url,{headers:ua}); if(!r.ok) continue; html=await r.text();}catch{continue}
   const ids=[...new Set([...html.matchAll(/\/itm\/(?:[^"'?/]+\/)?(\d{9,15})/g)].map(m=>m[1]))];
   for(const id of ids){
    if(rows.length>=TARGET||seen.has(id)) continue;
    let item=''; try{const r=await fetch(`https://www.ebay.com/itm/${id}`,{headers:ua}); if(!r.ok) continue; item=await r.text();}catch{continue}
    const text=txt(item);
    if(!/(This listing sold on|This item was sold|\bSOLD\b)/i.test(text)) continue;
    const title=decode(item.match(/<title>(.*?)<\/title>/i)?.[1]||'').replace(/\s*\|\s*eBay.*$/i,'').trim();
    if(!/shirt|t-?shirt|tee|hoodie|sweatshirt|cap|hat/i.test(title)) continue;
    const price=text.match(/(?:US |AU |C )?\$([0-9,]+(?:\.\d{2})?)/)?.[1];
    const pics=[...item.matchAll(/Picture \d+ of (\d+)/g)].map(m=>Number(m[1]));
    const soldDate=text.match(/(?:This listing sold on|This item was sold on)\s+([^.;]+?)(?:See original|Sell one|$)/i)?.[1]?.trim()||null;
    rows.push({id:`EBAY-NEXT100-${id}`,marketplace:'ebay',listing_id:id,sold:true,title,brand,tradition,era_claim:era,sold_price:price?Number(price.replace(/,/g,'')):null,currency:/AU \$/.test(text)?'AUD':/C \$/.test(text)?'CAD':'USD',image_count:pics.length?Math.max(...pics):null,sold_date:soldDate,source_url:`https://www.ebay.com/itm/${id}`,retrieved:new Date().toISOString().slice(0,10),collector:'ebay-completed-search-verified'});
    seen.add(id); await sleep(150);
   }
   await sleep(250);
  }
 }
 if(rows.length>=TARGET) break;
}
if(rows.length!==TARGET) throw new Error(`Only collected ${rows.length}/${TARGET} unique verified sold listings`);
await writeFile(OUT,rows.map(r=>JSON.stringify(r)).join('\n')+'\n');
console.log(JSON.stringify({added:rows.length,out:OUT},null,2));
