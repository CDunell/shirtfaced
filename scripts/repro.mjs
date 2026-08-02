/**
 * Regression check: a cart saved by an older build must not crash /cart.
 *
 * CartLine gained colour/art/body/ink after release; carts written before that
 * crashed the route on `garment.name.replace(...)`, which also trapped the
 * user because they couldn't reach the remove button.
 *
 *   node scripts/repro.mjs
 */
import { spawn } from "node:child_process";
const CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORT=9366;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const chrome=spawn(CHROME,["--headless=new",`--remote-debugging-port=${PORT}`,"--disable-gpu","--no-first-run","--incognito","about:blank"],{stdio:"ignore"});
for(let i=0;i<40;i++){try{await(await fetch(`http://127.0.0.1:${PORT}/json/version`)).json();break}catch{await sleep(250)}}
const t=await(await fetch(`http://127.0.0.1:${PORT}/json/new?about:blank`,{method:"PUT"})).json();
const ws=new WebSocket(t.webSocketDebuggerUrl);let id=0;const p=new Map();const w=[];const logs=[];
ws.addEventListener("message",e=>{const m=JSON.parse(e.data);
  if(m.id&&p.has(m.id)){p.get(m.id)(m.result);p.delete(m.id)}
  else if(m.method==="Runtime.exceptionThrown"){logs.push("EXCEPTION: "+(m.params.exceptionDetails.exception?.description||m.params.exceptionDetails.text).split("\n")[0])}
  else if(m.method==="Runtime.consoleAPICalled"&&m.params.type==="error"){logs.push("console.error: "+m.params.args.map(a=>a.value||a.description||"").join(" ").slice(0,200))}
  else if(m.method){for(let i=w.length-1;i>=0;i--)if(w[i].m===m.method){w[i].r(m.params);w.splice(i,1)}}});
await new Promise(r=>ws.addEventListener("open",r));
const send=(method,params={})=>new Promise(res=>{const n=++id;p.set(n,res);ws.send(JSON.stringify({id:n,method,params}))});
const once=(m,ms=15000)=>Promise.race([new Promise(r=>w.push({m,r})),sleep(ms)]);
await send("Page.enable");await send("Runtime.enable");

// Seed a cart in the OLD schema (pre colour/art/body/ink) then load /cart.
await send("Page.navigate",{url:"https://shirtfaced.wtf/"});
await once("Page.loadEventFired");await sleep(600);
await send("Runtime.evaluate",{expression:`localStorage.setItem('shirtfaced-cart', JSON.stringify([
  {slug:'classic-tee-black',name:'Classic Tee — Black',price:28,size:'M',quantity:1},
  {slug:'send-it-club-tee',name:'Send It Club Tee',price:49.95,size:'L',quantity:2},
  {slug:'roll-the-dice-tee',size:'XL'},
  null,
  {garbage:true}
]))`});
logs.length=0;
await send("Page.navigate",{url:"https://shirtfaced.wtf/cart"});
await once("Page.loadEventFired");await sleep(2000);
const {result}=await send("Runtime.evaluate",{expression:`document.body.innerText.slice(0,260)`,returnByValue:true});
console.log("BODY TEXT:", JSON.stringify(result.value));
console.log("ERRORS:", logs.length?logs.slice(0,4).join("\n  "):"(none)");
ws.close();chrome.kill();
