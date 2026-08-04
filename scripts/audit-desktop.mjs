/**
 * Desktop layout audit. Catches the class of defect that only shows on wide
 * screens: gaps where a background should be continuous, and controls that
 * stretch to absurd widths because nothing caps them.
 *
 *   node scripts/audit-desktop.mjs [url] [width]
 */
import { spawn } from "node:child_process";
const CHROME = process.env.CHROME_PATH || "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT = 9451;
const sleep = ms => new Promise(r => setTimeout(r, ms));
const c = spawn(CHROME,["--headless=new",`--remote-debugging-port=${PORT}`,"--disable-gpu","--hide-scrollbars","--no-first-run","--incognito","about:blank"],{stdio:"ignore"});
for (let i=0;i<40;i++){try{await(await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();break}catch{await sleep(250)}}
const t = await (await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`,{method:"PUT"})).json();
const ws = new WebSocket(t.webSocketDebuggerUrl); let id=0; const p=new Map(); const w=[];
ws.addEventListener("message",e=>{const m=JSON.parse(e.data);if(m.id&&p.has(m.id)){p.get(m.id)(m.result);p.delete(m.id)}else if(m.method){for(let i=w.length-1;i>=0;i--)if(w[i].m===m.method){w[i].r(m.params);w.splice(i,1)}}});
await new Promise(r=>ws.addEventListener("open",r));
const send=(m,pr={})=>new Promise(r=>{const n=++id;p.set(n,r);ws.send(JSON.stringify({id:n,method:m,params:pr}))});
const once=(m,ms=20000)=>Promise.race([new Promise(r=>w.push({m,r})),sleep(ms)]);
const url = process.argv[2] || "https://shirtfaced.wtf/";
const W = Number(process.argv[3]) || 1900;
await send("Page.enable");
await send("Emulation.setDeviceMetricsOverride",{width:W,height:1000,deviceScaleFactor:1,mobile:false});
await send("Page.navigate",{url}); await once("Page.loadEventFired"); await sleep(2200);
const {result} = await send("Runtime.evaluate",{returnByValue:true,expression:`(()=>{
const issues=[];
// gaps between adjacent full-width sections — where a collapsed margin lets
// the body background show through a run of dark blocks
const secs=[...document.querySelectorAll('main > section, main > div > section')];
for(let i=0;i<secs.length-1;i++){
  const a=secs[i].getBoundingClientRect(), b=secs[i+1].getBoundingClientRect();
  const gap=Math.round(b.top-a.bottom);
  // Only a defect when both neighbours paint the SAME non-body background —
  // that's a run of dark blocks with the page showing through the seam.
  // Ordinary vertical rhythm between cream sections is not a defect.
  const bodyBg=getComputedStyle(document.body).backgroundColor;
  const bgA=getComputedStyle(secs[i]).backgroundColor;
  const bgB=getComputedStyle(secs[i+1]).backgroundColor;
  if(gap>0 && bgA===bgB && bgA!==bodyBg && !bgA.includes('rgba(0, 0, 0, 0)'))
    issues.push({type:'seam in a continuous background',gap,bg:bgA,after:secs[i].className.slice(0,40)});
}
// controls with no sensible cap
[...document.querySelectorAll('input,select,textarea')].forEach(e=>{
  const wd=Math.round(e.getBoundingClientRect().width);
  if(wd>560) issues.push({type:'stretched control',tag:e.tagName,width:wd});
});
return JSON.stringify({url:location.pathname,viewport:innerWidth,
 overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth,
 issues},null,1)})()`});
console.log(result.value);
ws.close(); c.kill();
