#!/usr/bin/env node
/**
 * Build/extend the vintage eBay sold-evidence corpus from search-engine indexed
 * eBay sold pages. This is deliberately evidence-first: a candidate is admitted
 * only when fetched page text explicitly says "This listing sold on" or exposes
 * an unambiguous SOLD marker. Existing listing IDs are de-duplicated.
 *
 * Search discovery is intentionally externalised via SEARXNG_URL because eBay's
 * own sold-search endpoint is bot-sensitive. Set SEARXNG_URL to any SearXNG JSON
 * endpoint, e.g. https://search.example/search, then run:
 *   SEARXNG_URL=... node scripts/collect-vintage-ebay-sold.mjs
 *
 * Output: docs/research/vintage-market-evidence/ebay-sold-auto.jsonl
 */
import { readFile, writeFile } from 'node:fs/promises';

const OUT='docs/research/vintage-market-evidence/ebay-sold-auto.jsonl';
const SEED='docs/research/vintage-market-evidence/ebay-sold.jsonl';
const endpoint=process.env.SEARXNG_URL;
if(!endpoint) throw new Error('SEARXNG_URL is required');

const brands=[
 ['Stussy','streetwear'],['Vision Street Wear','skate'],['Powell Peralta','skate'],
 ['Santa Cruz','skate'],['Independent Trucks','skate'],['Thrasher','skate'],
 ['Airwalk','skate'],['Alien Workshop','skate'],['World Industries','skate'],
 ['Blind Skateboards','skate'],['Hook Ups','skate'],['Freshjive','streetwear'],
 ['Gotcha','surf'],['Mambo','australian-surf-street'],['Quiksilver','surf'],
 ['Billabong','surf'],['Rusty','surf'],['Rip Curl','surf'],['T&C Surf Designs','surf'],
 ['Ocean Pacific','surf'],['Mossimo','streetwear'],['No Fear','streetwear'],
 ['Bad Boy Club','surf-skate'],['Volcom','skate'],['Hobie','surf']
];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const existing=new Set();
for(const file of [SEED,OUT]){try{for(const l of (await readFile(file,'utf8')).trim().split(/\n+/)){if(l) existing.add(JSON.parse(l).listing_id)}}catch{}}
const rows=[];
const ua={'user-agent':'Mozilla/5.0 (compatible; shirtfaced-design-research/1.0)'};

for(const [brand,tradition] of brands){
 for(const era of ['80s','90s','Y2K']){
  const q=`site:ebay.com/itm "This listing sold" vintage ${brand} ${era} shirt t-shirt`;
  const u=new URL(endpoint); u.searchParams.set('q',q);u.searchParams.set('format','json');
  let search; try{search=await (await fetch(u,{headers:ua})).json()}catch{continue}
  for(const hit of search.results||[]){
   const m=String(hit.url||'').match(/ebay\.com\/itm\/(\d+)/); if(!m||existing.has(m[1])) continue;
   let html; try{html=await (await fetch(`https://www.ebay.com/itm/${m[1]}`,{headers:ua})).text()}catch{continue}
   const text=html.replace(/<script[\s\S]*?<\/script>/gi,' ').replace(/<style[\s\S]*?<\/style>/gi,' ').replace(/<[^>]+>/g,' ').replace(/&nbsp;/g,' ').replace(/&amp;/g,'&').replace(/\s+/g,' ');
   if(!/This listing sold on|\bSOLD\b/i.test(text)) continue;
   const title=(html.match(/<title>(.*?)<\/title>/i)?.[1]||hit.title||'').replace(/\s*\|\s*eBay.*$/i,'').trim();
   const price=text.match(/(?:US |AU )?\$([0-9,]+(?:\.\d{2})?)/)?.[1]?.replace(',','');
   const pics=[...html.matchAll(/Picture \d+ of (\d+)/g)].map(x=>+x[1]);
   const soldDate=text.match(/This listing sold on ([^.]+?)(?:See original listing|Sell one like this|Image:)/i)?.[1]?.trim();
   const rec={id:`EBAY-AUTO-${m[1]}`,marketplace:'ebay',listing_id:m[1],sold:true,title,brand,tradition,era_claim:era,sold_price:price?Number(price):null,currency:/AU \$/.test(text)?'AUD':'USD',image_count:pics.length?Math.max(...pics):null,sold_date:soldDate||null,source_url:`https://www.ebay.com/itm/${m[1]}`,retrieved:new Date().toISOString().slice(0,10),collector:'automated-search-verified'};
   rows.push(rec);existing.add(m[1]);
   if(existing.size>=500) break;
   await sleep(350);
  }
  if(existing.size>=500) break;
  await sleep(500);
 }
 if(existing.size>=500) break;
}
let prior='';try{prior=await readFile(OUT,'utf8')}catch{}
const merged=prior+(prior&&!prior.endsWith('\n')?'\n':'')+rows.map(r=>JSON.stringify(r)).join('\n')+(rows.length?'\n':'');
await writeFile(OUT,merged);
console.log(JSON.stringify({existing_before:existing.size-rows.length,added:rows.length,total:existing.size,target:500},null,2));
