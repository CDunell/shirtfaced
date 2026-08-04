/**
 * Measure each hero tagline and report the cqw size that makes it fill the
 * hero width. Anton is single-weight, so line length alone decides how wide a
 * string renders — the sizes in lib/taglines.ts have to be measured, not
 * guessed, or short lines strand whitespace and long ones overflow.
 *
 *   node scripts/tune-taglines.mjs [url]
 */
import { spawn } from "node:child_process";
const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9471;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const c = spawn(CHROME,["--headless=new",`--remote-debugging-port=${PORT}`,"--disable-gpu","--hide-scrollbars","--no-first-run","--incognito","about:blank"],{stdio:"ignore"});
for (let i=0;i<40;i++){try{await(await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();break}catch{await sleep(250)}}
const t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`,{method:"PUT"})).json();
const ws = new WebSocket(t.webSocketDebuggerUrl); let id=0; const p=new Map(); const w=[];
ws.addEventListener("message",e=>{const m=JSON.parse(e.data);if(m.id&&p.has(m.id)){p.get(m.id)(m.result);p.delete(m.id)}else if(m.method){for(let i=w.length-1;i>=0;i--)if(w[i].m===m.method){w[i].r(m.params);w.splice(i,1)}}});
await new Promise(r=>ws.addEventListener("open",r));
const send=(m,pr={})=>new Promise(r=>{const n=++id;p.set(n,r);ws.send(JSON.stringify({id:n,method:m,params:pr}))});
const once=(m,ms=20000)=>Promise.race([new Promise(r=>w.push({m,r})),sleep(ms)]);
await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride",{width:1440,height:900,deviceScaleFactor:1,mobile:false});
await send("Page.navigate",{url:process.argv[2]||"https://shirtfaced.wtf/"});
await once("Page.loadEventFired"); await sleep(2500);

// Target: the widest of the two fixed lines, so all three read as one block.
const {result} = await send("Runtime.evaluate",{returnByValue:true,expression:`(async()=>{
 await document.fonts.ready;
 const hero=document.querySelector('.hero-img');
 const box=hero.clientWidth;
 const spans=[...document.querySelector('h1').children];
 const fixed=[spans[0],spans[2]].map(e=>({t:e.textContent.trim(),
   w:e.firstChild?e.getBoundingClientRect().width:0,
   size:parseFloat(getComputedStyle(e).fontSize)}));
 // measure fixed lines by their text width
 const measure=(el)=>{const r=document.createRange();r.selectNodeContents(el);return r.getBoundingClientRect().width};
 const f=[spans[0],spans[2]].map(e=>({t:e.textContent.trim(),w:measure(e),cqw:parseFloat(e.style.fontSize)}));
 const target=Math.max(...f.map(x=>x.w));
 const out=[];
 for(const el of document.querySelectorAll('.tl')){
   const prev=el.style.display; el.style.display='block';
   const wdt=measure(el); const cqw=parseFloat(el.style.fontSize);
   el.style.display=prev;
   out.push({line:el.textContent.trim(),cqw,width:Math.round(wdt),suggested:+(cqw*target/wdt).toFixed(1)});
 }
 return JSON.stringify({box,target:Math.round(target),fixed:f.map(x=>({t:x.t,w:Math.round(x.w),cqw:x.cqw})),lines:out},null,1)})()`,awaitPromise:true});
console.log(result.value);
ws.close(); c.kill();
