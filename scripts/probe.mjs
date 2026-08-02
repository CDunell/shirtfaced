import { spawn } from "node:child_process";
const CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT=9344;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(CHROME,["--headless=new",`--remote-debugging-port=${PORT}`,"--disable-gpu","--no-first-run","--incognito","about:blank"],{stdio:"ignore"});
let v;for(let i=0;i<40;i++){try{v=await(await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();break}catch{await sleep(250)}}
const t=await(await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`,{method:"PUT"})).json();
const ws=new WebSocket(t.webSocketDebuggerUrl);let id=0;const p=new Map();const w=[];
ws.addEventListener("message",e=>{const m=JSON.parse(e.data);if(m.id&&p.has(m.id)){p.get(m.id)(m.result);p.delete(m.id)}else if(m.method){for(let i=w.length-1;i>=0;i--)if(w[i].m===m.method){w[i].r(m.params);w.splice(i,1)}}});
await new Promise(r=>ws.addEventListener("open",r));
const send=(method,params={})=>new Promise(res=>{const n=++id;p.set(n,res);ws.send(JSON.stringify({id:n,method,params}))});
const once=(m,ms=15000)=>Promise.race([new Promise(r=>w.push({m,r})),sleep(ms)]);
await send("Page.enable");await send("Network.enable");await send("Network.clearBrowserCache");
await send("Page.navigate",{url:process.argv[2]});
await once("Page.loadEventFired");await sleep(1200);
const {result}=await send("Runtime.evaluate",{expression:`(()=>{const i=document.querySelector('header img[alt="Shirtfaced"]');return JSON.stringify({src:i&&i.currentSrc,nw:i&&i.naturalWidth,nh:i&&i.naturalHeight,attrW:i&&i.getAttribute('width')})})()`,returnByValue:true});
console.log(result.value);
ws.close();chrome.kill();
