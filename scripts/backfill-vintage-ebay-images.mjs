#!/usr/bin/env node
/**
 * Backfill listing images for every vintage-market-evidence JSONL record.
 * Images are research evidence and are NOT committed to this public repo.
 * They are written to a private cache root supplied by VINTAGE_IMAGE_ROOT.
 *
 * Layout:
 *   <root>/<listing_id>/record.json
 *   <root>/<listing_id>/image-01.jpg ...
 *   <root>/<listing_id>/provenance.json
 */
import { mkdir, readdir, readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import path from 'node:path';

const ROOT=process.env.VINTAGE_IMAGE_ROOT;
if(!ROOT) throw new Error('VINTAGE_IMAGE_ROOT is required');
const EVIDENCE='docs/research/vintage-market-evidence';
const UA={'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/131 Safari/537.36'};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

async function filesRecursive(dir){
 const out=[];
 for(const ent of await readdir(dir,{withFileTypes:true})){
  const p=path.join(dir,ent.name);
  if(ent.isDirectory()) out.push(...await filesRecursive(p));
  else if(ent.isFile() && ent.name.endsWith('.jsonl')) out.push(p);
 }
 return out;
}
function decode(s=''){return s.replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/\\u0026/g,'&').replace(/\\\//g,'/');}
function bestImageUrls(html){
 const found=[];
 const add=u=>{u=decode(u||''); if(!/^https:\/\/i.ebayimg.com\//.test(u)) return; u=u.replace(/s-l\d+\.(jpg|jpeg|png|webp)(\?.*)?$/i,'s-l1600.$1'); if(!found.includes(u)) found.push(u)};
 for(const m of html.matchAll(/https:\/\/i\.ebayimg\.com\/images\/g\/[A-Za-z0-9_-]+\/s-l\d+\.(?:jpg|jpeg|png|webp)/gi)) add(m[0]);
 for(const m of html.matchAll(/"zoomUrl":"([^"]+)"/g)) add(m[1]);
 for(const m of html.matchAll(/"imageUrl":"([^"]+)"/g)) add(m[1]);
 return found;
}

const allFiles=await filesRecursive(EVIDENCE);
const records=new Map();
for(const file of allFiles){
 const text=await readFile(file,'utf8');
 for(const line of text.split(/\n+/)){
  if(!line.trim()) continue;
  try{const r=JSON.parse(line); if(r.listing_id && r.sold===true && !records.has(String(r.listing_id))) records.set(String(r.listing_id),r)}catch{}
 }
}
let savedListings=0,savedImages=0,failed=0;
for(const [id,record] of records){
 const dir=path.join(ROOT,id); await mkdir(dir,{recursive:true});
 let html='';
 try{const res=await fetch(record.source_url||`https://www.ebay.com/itm/${id}`,{headers:UA}); if(!res.ok) throw new Error(String(res.status)); html=await res.text()}catch{failed++;continue}
 const urls=bestImageUrls(html);
 const prov=[]; let n=0;
 for(const url of urls){
  try{
   const res=await fetch(url,{headers:UA}); if(!res.ok) continue;
   const buf=Buffer.from(await res.arrayBuffer()); if(buf.length<5000) continue;
   n++; const ext=(res.headers.get('content-type')||'image/jpeg').includes('png')?'png':'jpg';
   const name=`image-${String(n).padStart(2,'0')}.${ext}`; await writeFile(path.join(dir,name),buf);
   prov.push({file:name,source_url:url,sha256:createHash('sha256').update(buf).digest('hex'),byte_size:buf.length,content_type:res.headers.get('content-type')||null,acquired_at:new Date().toISOString()});
  }catch{}
 }
 await writeFile(path.join(dir,'record.json'),JSON.stringify({...record,stored_image_count:n},null,2));
 await writeFile(path.join(dir,'provenance.json'),JSON.stringify(prov,null,2));
 if(n){savedListings++;savedImages+=n}else failed++;
 await sleep(120);
}
await writeFile(path.join(ROOT,'manifest.json'),JSON.stringify({generated_at:new Date().toISOString(),listing_count:records.size,listings_with_images:savedListings,image_count:savedImages,failed},null,2));
console.log(JSON.stringify({records:records.size,listings_with_images:savedListings,image_count:savedImages,failed},null,2));
