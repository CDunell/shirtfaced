import { useEffect, useState } from "react";
import { useStyletron } from "baseui";

interface Evidence { listing_id:string; title?:string; brand?:string; images:string[] }
interface Concept { concept_number:number; title:string; idea:string; pass2_prompt:string; edited_prompt?:string; status:string }
interface Run { id:string; evidence_images:{image_url:string;filename:string}[]; concepts:Concept[] }

export function VintageResearchBench(): React.JSX.Element {
  const [css] = useStyletron();
  const [evidence,setEvidence]=useState<Evidence[]>([]);
  const [selected,setSelected]=useState<string[]>([]);
  const [run,setRun]=useState<Run|null>(null);
  const [busy,setBusy]=useState(false);
  const [q,setQ]=useState("");
  const load=async()=>{const r=await fetch(`/api/vintage-design/evidence?q=${encodeURIComponent(q)}`); if(r.ok)setEvidence(await r.json() as Evidence[])};
  useEffect(()=>{void load()},[]);
  const start=async()=>{setBusy(true);try{const r=await fetch("/api/vintage-design/runs",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({filters:{query:q},listing_ids:selected,image_limit:16})});if(!r.ok)throw new Error(await r.text());setRun(await r.json() as Run)}finally{setBusy(false)}};
  const review=async(n:number,status:string,edited_prompt?:string)=>{const r=await fetch(`/api/vintage-design/runs/${run?.id}/concepts/${n}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({status,edited_prompt})});if(r.ok)setRun(await r.json() as Run)};
  return <section>
    <h1 className="display">Vintage Research</h1>
    <p>Choose verified sold evidence, then run the two-pass visual research engine over the actual cached images.</p>
    {!run ? <>
      <div className={css({display:"flex",gap:"8px",marginBottom:"16px"})}><input aria-label="Search evidence" value={q} onChange={e=>setQ(e.target.value)} placeholder="Search evidence"/><button onClick={()=>void load()}>Filter</button><button disabled={busy||selected.length===0} onClick={()=>void start()}>{busy?"Running…":"Run both passes"}</button></div>
      <div className={css({display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(180px,1fr))",gap:"12px"})}>{evidence.map(e=><label key={e.listing_id} className={css({border:"1px solid #bbb",borderRadius:"12px",padding:"8px"})}><input type="checkbox" checked={selected.includes(e.listing_id)} onChange={()=>setSelected(s=>s.includes(e.listing_id)?s.filter(x=>x!==e.listing_id):[...s,e.listing_id])}/>{e.images[0]?<img src={e.images[0]} alt="" className={css({width:"100%",height:"150px",objectFit:"contain"})}/>:null}<strong>{e.brand??"Unknown"}</strong><div>{e.title}</div></label>)}</div>
    </> : <>
      <button onClick={()=>setRun(null)}>New research run</button>
      <h2>Exact source images</h2><div className={css({display:"flex",gap:"8px",overflowX:"auto"})}>{run.evidence_images.map(i=><img key={i.filename} src={i.image_url} alt={i.filename} className={css({width:"110px",height:"110px",objectFit:"contain"})}/>)}</div>
      <div className={css({display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(320px,1fr))",gap:"12px",marginTop:"20px"})}>{run.concepts.map(c=><ConceptCard key={c.concept_number} concept={c} onSave={(status,prompt)=>void review(c.concept_number,status,prompt)}/>)}</div>
    </>}
  </section>
}

function ConceptCard({concept,onSave}:{concept:Concept;onSave:(status:string,prompt:string)=>void}){
 const [prompt,setPrompt]=useState(concept.edited_prompt||concept.pass2_prompt);return <article><h3>{concept.concept_number}. {concept.title}</h3><p>{concept.idea}</p><textarea aria-label={`Prompt ${concept.concept_number}`} rows={12} value={prompt} onChange={e=>setPrompt(e.target.value)} style={{width:"100%"}}/><p>Status: <b>{concept.status}</b></p><div><button onClick={()=>onSave("approved",prompt)}>Approve</button> <button onClick={()=>onSave("rejected",prompt)}>Reject</button> <button onClick={()=>onSave(concept.status,prompt)}>Save edit</button></div></article>
}
