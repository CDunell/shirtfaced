#!/usr/bin/env node
/**
 * Extend the vintage eBay sold-evidence corpus without external search services.
 * Discovery uses eBay completed/sold search pages directly. A candidate is only
 * admitted after its item page exposes explicit sold evidence. Listing IDs are
 * deduplicated against both the hand-curated seed and automated output.
 */
import { readFile, writeFile } from 'node:fs/promises';

const OUT='docs/research/vintage-market-evidence/ebay-sold-auto.jsonl';
const SEED='docs/research/vintage-market-evidence/ebay-sold.jsonl';
const TARGET=500;
const brands=[
 ['Stussy','streetwear'],['Vision Street Wear','skate'],['Powell Peralta','skate'],['Santa Cruz','skate'],
 ['Independent Trucks','skate'],['Thrasher','skate'],['Airwalk','skate'],['Alien Workshop','skate'],
 ['World Industries','skate'],['Blind Skateboards','skate'],['Hook Ups','skate'],['Freshjive','streetwear'],
 ['Gotcha','surf'],['Mambo','australian-surf-street'],['Quiksilver','surf'],['Billabong','surf'],['Rusty','surf'],
 ['Rip Curl','surf'],['T&C Surf Designs','surf'],['Ocean Pacific','surf'],['Mossimo','streetwear'],['No Fear','streetwear'],
 ['Bad Boy Club','surf-skate'],['Volcom','skate'],['Hobie','surf'],['Hurley','surf'],['DC Shoes','skate'],
 ['Element','skate'],['Etnies','skate'],['Independent','skate'],['Zero Skateboards','skate'],['Toy Machine','skate']
];
const ua={'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36'};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const existing=new Set();
for(const file of [SEED,OUT]){try{for(const line of (await readFile(file,'utf8')).split(/\n+/)){if(line.trim()) existing.add(String(JSON.parse(line).listing_id))}}catch{}}
const rows=[];

function decode(s=''){return s.replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>');}
function textOf(html){return decode(html.replace(/<script[\s\S]*?<\/script>/gi,' ').replace(/<style[\s\S]*?<\/style>/gi,' ').replace(/<[^>]+>/g,' ').replace(/\s+/g,' '));}

for(const [brand,tradition] of brands){
 for(const era of ['80s','90s','2000s','Y2K']){
  for(let page=1;page<=8 && existing.size<TARGET;page++){
   const q=encodeURIComponent(`vintage ${brand} ${era} shirt t-shirt`);
   const searchUrl=`https://www.ebay.com/sch/i.html?_nkw=${q}&LH_Sold=1&LH_Complete=1&_pgn=${page}&_ipg=120`;
   let html=''; try{const r=await fetch(searchUrl,{headers:ua}); if(!r.ok) continue; html=await r.text()}catch{continue}
   const ids=[...new Set([...html.matchAll(/\/itm\/(?:[^"'?/]+\/)?(\d{9,15})/g)].map(m=>m[1]))];
   for(const id of ids){
    if(existing.has(id)||existing.size>=TARGET) continue;
    let item=''; try{const r=await fetch(`https://www.ebay.com/itm/${id}`,{headers:ua}); if(!r.ok) continue; item=await r.text()}catch{continue}
    const text=textOf(item);
    if(!/(This listing sold on|This item was sold|\bSOLD\b)/i.test(text)) continue;
    const title=decode(item.match(/<title>(.*?)<\/title>/i)?.[1]||'').replace(/\s*\|\s*eBay.*$/i,'').trim();
    if(!title||!/shirt|t-?shirt|tee|sweatshirt|hoodie|cap|hat/i.test(title)) continue;
    const soldDate=text.match(/(?:This listing sold on|This item was sold on)\s+([^.;]+?)(?:See original|Sell one|$)/i)?.[1]?.trim()||null;
    const priceMatch=text.match(/(?:US |AU )?\$([0-9,]+(?:\.\d{2})?)/);
    const pics=[...item.matchAll(/Picture \d+ of (\d+)/g)].map(m=>Number(m[1]));
    const rec={id:`EBAY-AUTO-${id}`,marketplace:'ebay',listing_id:id,sold:true,title,brand,tradition,era_claim:era,sold_price:priceMatch?Number(priceMatch[1].replace(/,/g,'')):null,currency:/AU \$/.test(text)?'AUD':'USD',image_count:pics.length?Math.max(...pics):null,sold_date:soldDate,source_url:`https://www.ebay.com/itm/${id}`,retrieved:new Date().toISOString().slice(0,10),collector:'ebay-completed-search-verified'};
    rows.push(rec); existing.add(id); await sleep(180);
   }
   await sleep(350);
  }
 }
}
let prior='';try{prior=await readFile(OUT,'utf8')}catch{}
if(rows.length){const merged=prior+(prior&&!prior.endsWith('\n')?'\n':'')+rows.map(r=>JSON.stringify(r)).join('\n')+'\n';await writeFile(OUT,merged)}
console.log(JSON.stringify({added:rows.length,total:existing.size,target:TARGET,complete:existing.size>=TARGET},null,2));
