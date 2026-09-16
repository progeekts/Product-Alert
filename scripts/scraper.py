import json
import os
import re
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_FILE = os.path.join(ROOT, "data", "alertas.json")
HEADERS = {"User-Agent": "ProductAlertSpain/2.1 (+https://github.com/progeekts/Product-Alert)", "Accept-Language": "es-ES,es;q=0.9,en;q=0.5"}

SOURCES = [
 {"agency":"AESAN","category":"Alimentación","url":"https://www.aesan.gob.es/alertas/alertas-alimentarias","keywords":["alerta","advertencia","ampliación"]},
 {"agency":"AEMPS","category":"Medicamentos","url":"https://www.aemps.gob.es/comunicacion/alertas/alertas-farmaceuticas-y-retiradas-de-lotes-de-medicamentos-de-uso-humano-por-defectos-de-calidad/","keywords":["alerta","retirada","defecto de calidad"]},
 {"agency":"AEMPS","category":"Productos sanitarios","url":"https://www.aemps.gob.es/productos-sanitarios/acciones-informativas-productos-sanitarios/","keywords":["aemps informa","retirada","riesgo","fallo","defecto","cese de comercialización"]},
 {"agency":"AEMPS","category":"Cosméticos","url":"https://www.aemps.gob.es/comunicacion/notas-de-seguridad/acciones-informativas-notas-de-seguridad-cosmeticos-y-cuidado-personal/","keywords":["aemps informa","retirada","recuperación","cese de comercialización","riesgo"]},
 {"agency":"AEMPS","category":"Cosméticos","url":"https://www.aemps.gob.es/comunicacion/notas-de-seguridad/notas-informativas-de-seguridad-de-cosmeticos/","keywords":["retirada","recuperación","cese de comercialización","riesgo","seguridad"]},
]

MONTHS_ES={"enero":"01","febrero":"02","marzo":"03","abril":"04","mayo":"05","junio":"06","julio":"07","agosto":"08","septiembre":"09","setiembre":"09","octubre":"10","noviembre":"11","diciembre":"12"}
NOISE=("cookie","pill","error_outline","notifications","arrow_forward","picture_as_pdf")

def stable_id(agency,title,link): return hashlib.sha256(f"{agency}|{title}|{link}".encode()).hexdigest()[:20]
def clean_text(node): return " ".join(node.get_text(" ",strip=True).split()) if node else ""
def clean_title(text):
 text=(text or "").strip()
 for token in NOISE: text=re.sub(rf"^{re.escape(token)}\s+","",text,flags=re.I)
 text=re.sub(r"\s+(?:Ver más|Leer más|Más información)\s*$","",text,flags=re.I)
 return " ".join(text.split())
def normalize_date(text):
 t=" ".join((text or "").split())
 m=re.search(r"(\d{1,2})\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+(20\d{2})",t)
 if m and MONTHS_ES.get(m.group(2).lower()): return f"{m.group(3)}-{MONTHS_ES[m.group(2).lower()]}-{int(m.group(1)):02d}"
 m=re.search(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})",t)
 if m:return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
 m=re.search(r"(20\d{2})-(\d{2})-(\d{2})",t); return m.group(0) if m else ""
def extract_reference(text):
 for p in [r"\b((?:PS|COS),?\s*\d+/20\d{2})\b",r"\b(ES20\d{2}/\d+)\b",r"\b(\d{1,4}/20\d{2})\b"]:
  m=re.search(p,text,re.I)
  if m:return re.sub(r"\s+"," ",m.group(1)).strip()
 return ""
def extract_lots(text): return list(dict.fromkeys(x.rstrip(".,;) ") for x in re.findall(r"(?:lote|lotes|n[ºo]\.?\s*de\s*lote)\s*[:\-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})",text,re.I)))[:12]
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
 r=requests.get(url,headers=HEADERS,timeout=35); r.raise_for_status(); return BeautifulSoup(r.text,"html.parser")
def parse_generic(source):
 soup=get_soup(source["url"]); alerts=[]; seen=set()
 for a in soup.find_all("a",href=True):
  raw=clean_text(a); low=raw.lower()
  if len(raw)<20 or not any(k in low for k in source["keywords"]):continue
  href=urljoin(source["url"],a["href"])
  if href in seen or href.startswith(("javascript:","mailto:")):continue
  title=clean_title(raw)
  if len(title)<20:continue
  seen.add(href); context=clean_text(a.parent) if a.parent else title
  date=normalize_date(raw) or normalize_date(context); reference=extract_reference(raw) or extract_reference(context)
  alerts.append({"id":stable_id(source["agency"],title,href),"title":title,"agency":source["agency"],"category":source["category"],"date":date,"link":href,"description":title,"reference":reference,"risk":infer_risk(title),"severity":infer_severity(title),"status":"Publicada","lotes":extract_lots(raw),"barcodes":[]})
 return alerts

def dedupe(alerts):
 by_key={}
 for x in alerts:
  key=(x.get("agency",""),x.get("reference","").lower()) if x.get("reference") else (x.get("agency",""),x.get("link",""))
  old=by_key.get(key)
  if not old or (x.get("date","") >= old.get("date","")): by_key[key]=x
 return list(by_key.values())

def load_previous():
 try:
  with open(DATA_FILE,encoding="utf-8") as f: raw=json.load(f)
  return raw if isinstance(raw,dict) else {"meta":{},"alerts":raw}
 except Exception: return {"meta":{},"alerts":[]}

def previous_slice(previous, source):
 return [x for x in previous.get("alerts",[]) if x.get("agency")==source["agency"] and x.get("category")==source["category"]]

def main():
 os.makedirs(os.path.dirname(DATA_FILE),exist_ok=True); previous=load_previous(); collected=[]; source_status=[]
 for source in SOURCES:
  try:
   items=parse_generic(source); collected.extend(items)
   source_status.append({"agency":source["agency"],"category":source["category"],"url":source["url"],"ok":True,"stale":False,"items":len(items)})
   print(f"[{source['agency']} / {source['category']}] {len(items)} registros detectados")
  except Exception as exc:
   cached=previous_slice(previous,source); collected.extend(cached)
   source_status.append({"agency":source["agency"],"category":source["category"],"url":source["url"],"ok":False,"stale":True,"items":len(cached),"error":str(exc)[:250]})
   print(f"[{source['agency']} / {source['category']}] ERROR; se conservan {len(cached)} registros previos: {exc}")
 alerts=dedupe(collected); alerts.sort(key=lambda x:(x.get("date",""),x.get("title","")),reverse=True)
 payload={"meta":{"last_checked":datetime.now(timezone.utc).isoformat(),"sources":source_status,"count":len(alerts),"scope":"España","version":3,"note":"Información agregada desde fuentes oficiales. Si una fuente falla temporalmente, se conserva su último conjunto conocido y se marca como desactualizado. La publicación original prevalece siempre."},"alerts":alerts}
 with open(DATA_FILE,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(f"Registro actualizado: {len(alerts)} alertas únicas")
if __name__=="__main__":main()
