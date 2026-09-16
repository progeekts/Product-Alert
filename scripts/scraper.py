import json
import os
import re
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..")); DATA_FILE=os.path.join(ROOT,"data","alertas.json")
HEADERS={"User-Agent":"ProductAlertSpain/2.4 (+https://github.com/progeekts/Product-Alert)","Accept-Language":"es-ES,es;q=0.9,en;q=0.5"}
SOURCES=[
 {"id":"aesan_food","agency":"AESAN","category":"Alimentación","url":"https://www.aesan.gob.es/alertas/alertas-alimentarias","keywords":["alerta","advertencia","ampliación"],"min_items":1},
 {"id":"aemps_medicines","agency":"AEMPS","category":"Medicamentos","url":"https://www.aemps.gob.es/category/informa/alertas/medicamentosusohumano-2/","parser":"aemps_medicines","min_items":1},
 {"id":"aemps_devices","agency":"AEMPS","category":"Productos sanitarios","url":"https://www.aemps.gob.es/productos-sanitarios/acciones-informativas-productos-sanitarios/","keywords":["aemps informa","retirada","riesgo","fallo","defecto","cese de comercialización"],"min_items":1},
 {"id":"aemps_cosmetics_actions","agency":"AEMPS","category":"Cosméticos","url":"https://www.aemps.gob.es/comunicacion/notas-de-seguridad/acciones-informativas-notas-de-seguridad-cosmeticos-y-cuidado-personal/","keywords":["aemps informa","retirada","recuperación","cese de comercialización","riesgo"],"min_items":1},
 {"id":"aemps_cosmetics_notes","agency":"AEMPS","category":"Cosméticos","url":"https://www.aemps.gob.es/comunicacion/notas-de-seguridad/notas-informativas-de-seguridad-de-cosmeticos/","keywords":["retirada","recuperación","cese de comercialización","riesgo","seguridad"],"min_items":1}]
MONTHS_ES={"enero":"01","febrero":"02","marzo":"03","abril":"04","mayo":"05","junio":"06","julio":"07","agosto":"08","septiembre":"09","setiembre":"09","octubre":"10","noviembre":"11","diciembre":"12"}; NOISE=("cookie","pill","error_outline","notifications","arrow_forward","picture_as_pdf")
def stable_id(agency,title,link):return hashlib.sha256(f"{agency}|{title}|{link}".encode()).hexdigest()[:20]
def clean_text(node):return " ".join(node.get_text(" ",strip=True).split()) if node else ""
def clean_title(text):
 text=(text or "").strip()
 for token in NOISE:text=re.sub(rf"^{re.escape(token)}\s+","",text,flags=re.I)
 return " ".join(re.sub(r"\s+(?:Ver más|Leer más|Más información)\s*$","",text,flags=re.I).split())
def normalize_date(text):
 t=" ".join((text or "").split()); m=re.search(r"(\d{1,2})\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+(20\d{2})",t)
 if m and MONTHS_ES.get(m.group(2).lower()):return f"{m.group(3)}-{MONTHS_ES[m.group(2).lower()]}-{int(m.group(1)):02d}"
 m=re.search(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})",t)
 if m:return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
 m=re.search(r"(20\d{2})-(\d{2})-(\d{2})",t);return m.group(0) if m else ""
def extract_reference(text):
 for p in [r"\b(R[_ -]?\d{1,3}/20\d{2})\b",r"\b((?:PS|COS),?\s*\d+/20\d{2})\b",r"\b(ES20\d{2}/\d+)\b",r"\b(\d{1,4}/20\d{2})\b"]:
  m=re.search(p,text,re.I)
  if m:return re.sub(r"\s+"," ",m.group(1)).strip()
 return ""
def extract_lots(text):return list(dict.fromkeys(x.rstrip(".,;) ") for x in re.findall(r"(?:lote|lotes|n[ºo]\.?\s*de\s*lote)\s*[:\-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})",text,re.I)))[:20]
def field(text,*labels):
 for label in labels:
  m=re.search(rf"{label}\s*[:\-]?\s*(.+?)(?=\s+(?:N[ºo]\.?\s*de\s*alerta|Producto|Nombre|Marca|Lote|Defecto|Clasificaci[oó]n|Medidas?\s+cautelares?|Fecha)\s*[:\-]|$)",text,re.I)
  if m:return m.group(1).strip(" .;:")[:800]
 return ""
def infer_severity(title):
 t=title.lower()
 if any(x in t for x in ["salmonella","listeria","vidrio","asfixia","riesgo grave","retirada del mercado","suspensión de la administración","contaminación microbiológica"]):return "alta"
 if any(x in t for x in ["alérgeno","gluten","fallo","defecto","advertencia","riesgo","recuperación"]):return "media"
 return "informativa"
def infer_risk(title):
 t=title.lower()
 for n,l in [("salmonella","Salmonella"),("listeria","Listeria"),("gluten","Alérgeno / gluten"),("asfixia","Asfixia"),("contaminación microbiológica","Contaminación microbiológica"),("contaminación","Contaminación"),("defecto","Defecto de calidad"),("fallo","Fallo de producto"),("retirada","Retirada")]:
  if n in t:return l
 return ""
def get_soup(url):
 r=requests.get(url,headers=HEADERS,timeout=35);r.raise_for_status();return BeautifulSoup(r.text,"html.parser")
def parse_generic(source):
 soup=get_soup(source["url"]);alerts=[];seen=set()
 for a in soup.find_all("a",href=True):
  raw=clean_text(a);low=raw.lower()
  if len(raw)<20 or not any(k in low for k in source["keywords"]):continue
  href=urljoin(source["url"],a["href"])
  if href in seen or href.startswith(("javascript:","mailto:")):continue
  title=clean_title(raw)
  if len(title)<20:continue
  seen.add(href);context=clean_text(a.parent) if a.parent else title;date=normalize_date(raw) or normalize_date(context);reference=extract_reference(raw) or extract_reference(context)
  alerts.append({"id":stable_id(source["agency"],title,href),"source_id":source["id"],"title":title,"agency":source["agency"],"category":source["category"],"date":date,"link":href,"description":title,"reference":reference,"risk":infer_risk(title),"severity":infer_severity(title),"status":"Publicada","lotes":extract_lots(raw),"barcodes":[],"consumer_action":"Consulta la publicación oficial para conocer las medidas aplicables."})
 return alerts
def enrich_aemps_medicine(item):
 try:
  soup=get_soup(item["link"]);main=soup.find("main") or soup; text=clean_text(main)
  reference=extract_reference(text) or item.get("reference",""); product=field(text,r"Producto",r"Nombre(?:\s+del\s+producto)?"); defect=field(text,r"Defecto(?:\s+detectado)?",r"Motivo"); classification=field(text,r"Clasificaci[oó]n(?:\s+del\s+defecto)?"); measures=field(text,r"Medidas?\s+cautelares?",r"Medidas?\s+adoptadas?"); lots=extract_lots(text) or item.get("lotes",[])
  if product:item["product"]=product
  if defect:item["risk"]=defect;item["description"]=f"Defecto de calidad: {defect}"
  if classification:item["official_classification"]=classification
  if measures:item["measures"]=measures;item["consumer_action"]=measures
  item["reference"]=reference;item["lotes"]=lots;item["enriched_from_detail"]=True
 except Exception as exc:item["enriched_from_detail"]=False;item["enrichment_error"]=str(exc)[:160]
 return item
def parse_aemps_medicines(source):
 soup=get_soup(source["url"]);alerts=[];seen=set()
 for heading in soup.find_all(["h2","h3"]):
  a=heading.find("a",href=True)
  if not a:continue
  href=urljoin(source["url"],a["href"])
  if href in seen or "/informa/" not in href:continue
  title=clean_title(clean_text(a));container=heading.parent;context=clean_text(container)
  if len(title)<12 or "información adicional" in title.lower() or not (re.search(r"R[_ -]?\d{1,3}/20\d{2}",context,re.I) or "nº alerta" in context.lower()):continue
  seen.add(href);item={"id":stable_id("AEMPS",title,href),"source_id":source["id"],"title":title,"agency":"AEMPS","category":"Medicamentos","date":normalize_date(context),"link":href,"description":title,"reference":extract_reference(context),"risk":"Defecto de calidad","severity":"informativa","status":"Publicada","lotes":extract_lots(context),"barcodes":[],"consumer_action":"Consulta la publicación oficial para conocer las medidas aplicables."};alerts.append(enrich_aemps_medicine(item))
 return alerts
def parse_source(source):return parse_aemps_medicines(source) if source.get("parser")=="aemps_medicines" else parse_generic(source)
def dedupe(alerts):
 by_key={}
 for x in alerts:
  key=(x.get("agency",""),x.get("reference","").lower()) if x.get("reference") else (x.get("agency",""),x.get("link",""));old=by_key.get(key)
  if not old or x.get("date","")>=old.get("date",""):by_key[key]=x
 return list(by_key.values())
def load_previous():
 try:
  with open(DATA_FILE,encoding="utf-8") as f:raw=json.load(f)
  return raw if isinstance(raw,dict) else {"meta":{},"alerts":raw}
 except Exception:return {"meta":{},"alerts":[]}
def previous_slice(previous,source):
 exact=[x for x in previous.get("alerts",[]) if x.get("source_id")==source["id"]]
 if exact:return exact
 same=[s for s in SOURCES if s["agency"]==source["agency"] and s["category"]==source["category"]]
 return [x for x in previous.get("alerts",[]) if x.get("agency")==source["agency"] and x.get("category")==source["category"]] if len(same)==1 else []
def main():
 os.makedirs(os.path.dirname(DATA_FILE),exist_ok=True);previous=load_previous();collected=[];source_status=[]
 for source in SOURCES:
  checked=datetime.now(timezone.utc).isoformat()
  try:
   items=parse_source(source)
   if len(items)<source.get("min_items",0):raise RuntimeError(f"extracción sospechosa: {len(items)} registros, mínimo esperado {source['min_items']}")
   collected.extend(items);source_status.append({"id":source["id"],"agency":source["agency"],"category":source["category"],"url":source["url"],"ok":True,"stale":False,"items":len(items),"checked_at":checked,"last_success":checked});print(f"[{source['id']}] {len(items)} registros detectados")
  except Exception as exc:
   cached=previous_slice(previous,source);collected.extend(cached);old=next((s for s in previous.get("meta",{}).get("sources",[]) if s.get("id")==source["id"] or s.get("url")==source["url"]),{});source_status.append({"id":source["id"],"agency":source["agency"],"category":source["category"],"url":source["url"],"ok":False,"stale":True,"items":len(cached),"checked_at":checked,"last_success":old.get("last_success"),"error":str(exc)[:250]});print(f"[{source['id']}] ERROR; se conservan {len(cached)} registros previos: {exc}")
 alerts=dedupe(collected);alerts.sort(key=lambda x:(x.get("date",""),x.get("title","")),reverse=True);payload={"meta":{"last_checked":datetime.now(timezone.utc).isoformat(),"sources":source_status,"count":len(alerts),"scope":"España","version":6,"note":"Información agregada desde fuentes oficiales. Los campos de medidas y actuación del consumidor solo se muestran cuando proceden de la fuente oficial; en ausencia de instrucciones se remite a la publicación original."},"alerts":alerts}
 with open(DATA_FILE,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(f"Registro actualizado: {len(alerts)} alertas únicas")
if __name__=="__main__":main()
