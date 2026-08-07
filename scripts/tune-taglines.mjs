/**
 * Measure each hero tagline pair against the .tagline-box — the element the
 * type actually resolves cqw against. The third beat ("shirtfaced", #tagline-
 * fixed) is the only fixed line; the two rotating beats in each .tl pair are
 * fitted against its width. Anton is single-weight, so beat length alone
 * decides how wide a string renders — the sizeOne/sizeTwo values in
 * lib/taglines.ts have to be measured, not guessed, or short beats strand
 * whitespace and long ones overflow.
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

// Target: the fixed "shirtfaced" line's width — every rotating beat is fitted to it.
const {result} = await send("Runtime.evaluate",{returnByValue:true,expression:`(async()=>{
 await document.fonts.ready;
 const box=document.querySelector('.tagline-box').clientWidth;
 const measure=(el)=>{const r=document.createRange();r.selectNodeContents(el);return r.getBoundingClientRect().width};
 const fixedEl=document.getElementById('tagline-fixed');
 const fixed={t:fixedEl.textContent.trim(),w:measure(fixedEl),cqw:parseFloat(fixedEl.style.fontSize)};
 const target=fixed.w;
 const out=[];
 for(const wrap of document.querySelectorAll('.tl')){
   const prevDisplay=wrap.style.display; wrap.style.display='contents';
   const beats=[...wrap.children].map(el=>{
     const wdt=measure(el); const cqw=parseFloat(el.style.fontSize);
     return {t:el.textContent.trim(),width:Math.round(wdt),cqw,suggested:+(cqw*target/wdt).toFixed(1)};
   });
   wrap.style.display=prevDisplay;
   out.push({pair:beats});
 }
 return JSON.stringify({box,target:Math.round(target),fixed:{t:fixed.t,w:Math.round(fixed.w),cqw:fixed.cqw},pairs:out},null,1)})()`,awaitPromise:true});
console.log(result.value);
ws.close(); c.kill();
