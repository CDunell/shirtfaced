"""PacSun men's graphic-tee evidence collector.

Acquisition only: real catalogue facts, images and provenance. Selection hints are
used transiently to avoid a first-N sample; they are never persisted as analysis.
"""
from __future__ import annotations
import html, json, re, time, urllib.error, urllib.parse, urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable
from .collector import build_manifest, extension_for, provenance_record, utc_now, write_json
BRAND_SLUG="pacsun"; BRAND_NAME="PacSun"; SITE_URL="https://www.pacsun.com"; DEFAULT_START_URL=f"{SITE_URL}/mens/graphic-tees/"; REQUEST_DELAY=.45
USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
NOISE=re.compile(r"\b(pack|solid|blank|basic|polo|rugby|jersey|knit|sweater|hoodie|button[- ]?up|scallop)\b",re.I)
TEE=re.compile(r"\b(t[- ]?shirts?|tees?|muscle t[- ]?shirts?|oversized t[- ]?shirts?|cropped boxy t[- ]?shirts?)\b",re.I)
MECHANISMS=(("licensed",re.compile(r"metallica|star wars|godfather|eminem|wwe|ufc|marvel|south park|coca.?cola|ford|formula 1|the met|keith haring",re.I)),("sport",re.compile(r"ufc|wwe|nba|nfl|raiders|racing|formula|champion|rodman",re.I)),("music",re.compile(r"metallica|eminem|tour|metro boomin|band",re.I)),("art",re.compile(r"haring|floral|angel|cherub|art|met|paper wings",re.I)),("dark",re.compile(r"misery|ominous|reaper|skull|bloody|grunge|goth|saint",re.I)),("brand",re.compile(r"pacsun|script|logo|handstyles|field of study|nightlab|huf",re.I)),("character",re.compile(r"cat|cartoon|spider|character|south park",re.I)),("auto",re.compile(r"ford|mustang|formula|race|chopper",re.I)))
@dataclass
class Product:
    name:str; source_url:str; brand:str=""; price:str=""; description:str=""; image_urls:list[str]=field(default_factory=list)
    @property
    def slug(self):
        path=urllib.parse.urlparse(self.source_url).path.rstrip("/").split("/")[-1]; path=re.sub(r"\.html$","",path,flags=re.I)
        return re.sub(r"[^a-z0-9]+","-",path.lower()).strip("-") or re.sub(r"[^a-z0-9]+","-",self.name.lower()).strip("-")
def canonical_url(url,base=SITE_URL):
    p=urllib.parse.urlsplit(urllib.parse.urljoin(base,html.unescape(url))); return urllib.parse.urlunsplit((p.scheme or "https",p.netloc.lower(),p.path,"",""))
def page_url(url,base=SITE_URL):
    p=urllib.parse.urlsplit(urllib.parse.urljoin(base,html.unescape(url))); return urllib.parse.urlunsplit((p.scheme or "https",p.netloc.lower(),p.path,p.query,""))
def _fetch(url,attempts=3):
    # PacSun's WAF blocks with 403 intermittently under repeated requests rather
    # than deterministically -- a category fetch that succeeds in one run can be
    # blocked seconds later once enough requests have come from the same source.
    # A short backoff-and-retry survives that without pretending the block never
    # happens: it still raises on the final attempt.
    req=urllib.request.Request(url,headers={
        "User-Agent":USER_AGENT,
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,application/json,image/*;q=0.8,*/*;q=0.7",
        "Accept-Language":"en-US,en;q=0.9",
    })
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req,timeout=35) as r:return r.read(),r.headers.get_content_type()
        except urllib.error.HTTPError as error:
            if error.code not in (403,429) or attempt==attempts-1:raise
            time.sleep(REQUEST_DELAY*(4**(attempt+1)))
def _jsonld(markup):
    rows=[]
    for raw in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',markup,re.I|re.S):
        try:value=json.loads(html.unescape(raw).strip())
        except (ValueError,TypeError):continue
        for item in value if isinstance(value,list) else [value]:
            if isinstance(item,dict):
                rows.append(item); graph=item.get("@graph")
                if isinstance(graph,list):rows.extend(x for x in graph if isinstance(x,dict))
    return rows
def parse_category(markup,page):
    products={}
    for href,label in re.findall(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',markup,re.I|re.S):
        text=html.unescape(re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",label))).strip(); url=canonical_url(href,page)
        if "pacsun.com" in urllib.parse.urlsplit(url).netloc and re.search(r"\.html$|/product/|/products/",urllib.parse.urlsplit(url).path,re.I) and TEE.search(text):products.setdefault(url,Product(text,url))
    for node in _jsonld(markup):
        if str(node.get("@type","")).lower()=="itemlist":
            for entry in node.get("itemListElement") or []:
                item=entry.get("item") if isinstance(entry,dict) else None
                if isinstance(item,dict):
                    url=canonical_url(str(item.get("url") or ""),page); name=str(item.get("name") or "").strip()
                    if url and name and TEE.search(name):products.setdefault(url,Product(name,url))
    m=re.search(r'<a[^>]+(?:rel=["\']next["\']|class=["\'][^"\']*(?:next|load-more)[^"\']*["\'])[^>]+href=["\']([^"\']+)',markup,re.I)
    return list(products.values()),page_url(m.group(1),page) if m else None
def is_graphic_candidate(p):return bool(TEE.search(p.name)) and not bool(NOISE.search(p.name))
def parse_product(markup,source_url,fallback_name=""):
    p=Product(fallback_name,canonical_url(source_url))
    for node in _jsonld(markup):
        if str(node.get("@type","")).lower()!="product":continue
        p.name=str(node.get("name") or p.name).strip(); brand=node.get("brand"); p.brand=str(brand.get("name") if isinstance(brand,dict) else brand or "").strip()
        p.description=html.unescape(re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",str(node.get("description") or "")))).strip(); images=node.get("image") or []; images=[images] if isinstance(images,str) else images
        p.image_urls.extend(str(u) for u in images if u); offers=node.get("offers"); offer=offers[0] if isinstance(offers,list) and offers else offers
        if isinstance(offer,dict) and (offer.get("price") or offer.get("lowPrice")):p.price=f"{offer.get('priceCurrency') or 'USD'} {offer.get('price') or offer.get('lowPrice')}"
        break
    for url in re.findall(r'https?://[^"\'\s,>]+\.(?:jpe?g|png|webp)(?:\?[^"\'\s,>]*)?',markup,re.I):
        if any(x in url.lower() for x in ("pacsun","scene7","demandware")):p.image_urls.append(html.unescape(url))
    p.image_urls=list(dict.fromkeys(p.image_urls)); return p
def select_images(urls:Iterable[str],maximum=3):
    unique=list(dict.fromkeys(urls)); picked=[]
    for hint in ("front","back","detail","alternate","alt"):
        m=next((u for u in unique if hint in u.lower() and u not in picked),None)
        if m:picked.append(m)
    for u in unique:
        if len(picked)>=maximum:break
        if u not in picked and not re.search(r"swatch|thumbnail|icon",u,re.I):picked.append(u)
    return picked[:maximum]
def select_sample(candidates,limit):
    selected=[]; used=set()
    for _,pattern in MECHANISMS:
        m=next((p for p in candidates if p.source_url not in used and pattern.search(f"{p.brand} {p.name}")),None)
        if m:selected.append(m);used.add(m.source_url)
        if len(selected)>=limit:return selected
    rem=[p for p in candidates if p.source_url not in used]; step=max(1,len(rem)//max(1,limit-len(selected))) if rem else 1
    for p in rem[::step]:
        if len(selected)>=limit:break
        selected.append(p);used.add(p.source_url)
    return selected
def discover(start_url=DEFAULT_START_URL,max_pages=50,fetch:Callable=_fetch):
    products={};failures=[];url=page_url(start_url);seen=set();pages=0
    while url and url not in seen and pages<max_pages:
        seen.add(url);pages+=1
        try:body,_=fetch(url);rows,nxt=parse_category(body.decode("utf-8",errors="replace"),url)
        except Exception as exc:failures.append({"url":url,"error":f"{type(exc).__name__}: {exc}"});break
        for row in rows:products.setdefault(row.source_url,row)
        url=nxt;time.sleep(REQUEST_DELAY)
    return list(products.values()),failures
def enrich(products,fetch:Callable=_fetch):
    out=[];fail=[]
    for stub in products:
        try:body,_=fetch(stub.source_url);out.append(parse_product(body.decode("utf-8",errors="replace"),stub.source_url,stub.name))
        except Exception as exc:fail.append({"url":stub.source_url,"error":f"{type(exc).__name__}: {exc}"})
        time.sleep(REQUEST_DELAY)
    return out,fail
def acquire(selected,root:Path,refresh=False,fetch:Callable=_fetch):
    brand=root/BRAND_SLUG;write_json(brand/"brand.json",{"brand_slug":BRAND_SLUG,"brand_name":BRAND_NAME,"site_url":SITE_URL,"acquired_at":utc_now(),"notes":"Current-market men's graphic tee evidence sample."})
    hashes={};saved_products=saved_images=0;fail=[]
    for p in selected:
        d=brand/"products"/p.slug
        if d.exists() and not refresh:continue
        d.mkdir(parents=True,exist_ok=True);source_id=f"{BRAND_SLUG}/{p.slug}";files=[];prov=[]
        for source in select_images(p.image_urls):
            try:data,ctype=fetch(source)
            except Exception as exc:fail.append({"url":source,"error":f"{type(exc).__name__}: {exc}"});continue
            rec=provenance_record(source_id=source_id,image_stem=f"image-{len(files)+1:02d}",source_url=source,data=data,content_type=ctype);digest=str(rec["content_hash"])
            if digest in hashes:continue
            ext=extension_for(ctype,source);name=f"image-{len(files)+1:02d}{ext}";(d/name).write_bytes(data);hashes[digest]=d/name;files.append(name);prov.append(rec);saved_images+=1;time.sleep(REQUEST_DELAY)
        if not files:fail.append({"url":p.source_url,"error":"no useful images downloaded"});continue
        write_json(d/"product.json",{"product_id":source_id,"brand_slug":BRAND_SLUG,"name":p.name,"source_url":p.source_url,"category":"tee","price":p.price,"description":p.description,"images":files,"acquired_at":utc_now()});write_json(d/"provenance.json",prov);saved_products+=1
    build_manifest(root);return saved_products,saved_images,fail
