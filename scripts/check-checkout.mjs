/** Measures the state/postcode row on /checkout at mobile width. */
import { spawn } from "node:child_process";
const CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT=9377;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(CHROME,["--headless=new",`--remote-debugging-port=${PORT}`,"--disable-gpu","--no-first-run","--incognito","about:blank"],{stdio:"ignore"});
for(let i=0;i<40;i++){try{await(await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();break}catch{await sleep(250)}}
const t=await(await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`,{method:"PUT"})).json();
const ws=new WebSocket(t.webSocketDebuggerUrl);let id=0;const p=new Map();const w=[];const errs=[];
ws.addEventListener("message",e=>{const m=JSON.parse(e.data);
 if(m.id&&p.has(m.id)){p.get(m.id)(m.result);p.delete(m.id)}
 else if(m.method==="Runtime.exceptionThrown"){errs.push(m.params.exceptionDetails.exception?.description?.split("\n")[0])}
 else if(m.method){for(let i=w.length-1;i>=0;i--)if(w[i].m===m.method){w[i].r(m.params);w.splice(i,1)}}});
await new Promise(r=>ws.addEventListener("open",r));
const send=(m,pr={})=>new Promise(r=>{const n=++id;p.set(n,r);ws.send(JSON.stringify({id:n,method:m,params:pr}))});
const once=(m,ms=15000)=>Promise.race([new Promise(r=>w.push({m,r})),sleep(ms)]);
await send("Page.enable");await send("Runtime.enable");
await send("Emulation.setDeviceMetricsOverride",{width:390,height:844,deviceScaleFactor:2,mobile:true});
await send("Page.navigate",{url:"https://shirtfaced.wtf/"});await once("Page.loadEventFired");await sleep(500);
await send("Runtime.evaluate",{expression:`localStorage.setItem('shirtfaced-cart',JSON.stringify([{slug:'send-it-club-tee',name:'Send It Club Tee',price:49.95,size:'L',colour:'Vintage White',art:'send-it',body:'#e8e2d5',ink:'#1c1c1a',quantity:1}]))`});
await send("Page.navigate",{url:"https://shirtfaced.wtf/checkout"});await once("Page.loadEventFired");await sleep(1500);
const {result}=await send("Runtime.evaluate",{returnByValue:true,expression:`(()=>{
 const sel=document.querySelector('select[autocomplete="address-level1"]');
 const pc=document.querySelector('input[autocomplete="postal-code"]');
 if(!sel||!pc) return JSON.stringify({error:'fields not found'});
 const s=sel.getBoundingClientRect(), p=pc.getBoundingClientRect();
 return JSON.stringify({
   selectWidth:Math.round(s.width), selectValue:sel.value,
   selectVisibleText:sel.options[sel.selectedIndex]?.text,
   postcodeWidth:Math.round(p.width),
   rowGap:Math.round(p.left-s.right),
   rightEdge:Math.round(p.right), viewport:document.documentElement.clientWidth,
   overflow:document.documentElement.scrollWidth-document.documentElement.clientWidth
 })})()`});
console.log(result.value);
console.log("errors:", errs.length?errs:"(none)");
ws.close();chrome.kill();
