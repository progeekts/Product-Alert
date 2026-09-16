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
HEADERS = {"User-Agent": "ProductAlertSpain/1.2 (+https://github.com/progeekts/Product-Alert)", "Accept-Language": "es-ES,es;q=0.9,en;q=0.5"}

SOURCES = [
 {"agency":"AESAN","category":"Alimentación","url":"https://www.aesan.gob.es/alertas/alertas-alimentarias","keywords":["alerta","advertencia","ampliación"]},
 {"agency":"AEMPS","category":"Medicamentos","url":"https://www.aemps.gob.es/comunicacion/alertas/alertas-farmaceuticas-y-retiradas-de-lotes-de-medicamentos-de-uso-humano-por-defectos-de-calidad/","keywords":["alerta","retirada","defecto de calidad"]},
 {"agency":"AEMPS","category":"Productos sanitarios","url":"https://www.aemps.gob.es/productos-sanitarios/acciones-informativas-productos-sanitarios/","keywords":["aemps informa","retirada","riesgo","fallo","defecto","cese de comercialización"]},
 {"agency":"AEMPS","category":"Cosméticos","url":"https://www.aemps.gob.es/comunicacion/notas-de-seguridad/acciones-informativas-notas-de-seguridad-cosmeticos-y-cuidado-personal/","keywords":["aemps informa","retirada","recuperación","cese de comercialización","riesgo"]},
]

MONTHS_ES={"enero":"01","febrero":"02","marzo":"03","abril":"04","mayo":"05","junio":"06","julio":"07","agosto":"08","septiembre":"09","setiembre":"09","octubre":"10","noviembre":"11","diciembre":"12"}

def stable_id(agency,title,link): return hashlib.sha256(f"{agency}|{title}|{link}".encode()).hexdigest()[:20]
def clean_text(node): return " ".join(node.get_text(" ",strip=True).split()) if node else ""
def clean_title(text):
 text=re.sub(r"^(?:cookie|pill|error_outline|notifications)\s+","",text.strip(),flags=re.I)
 return re.sub(r"\s+Ver más\s*$","",text,flags=re.I).strip()
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
def infer_severity(title,desc):
 t=f"{title} {desc}".lower()
 if any(x in t for x in ["salmonella","listeria","vidrio","asfixia","riesgo grave","retirada del mercado","suspensión de la administración"]):return "alta"
 if any(x in t for x in ["alérgeno","gluten","fallo","defecto","advertencia","riesgo"]):return "media"
 return "informativa"
def infer_risk(title):
 t=title.lower()
 for n,l in [("salmonella","Salmonella"),("listeria","Listeria"),("gluten","Alérgeno / gluten"),("asfixia","Asfixia"),("contaminación","Contaminación"),("defecto","Defecto de calidad"),("fallo","Fallo de producto"),("retirada","Retirada")]:
  if n in t:return l
 return ""
def get_soup(url):
 r=requests.get(url,headers=HEADERS,timeout=35); r.raise_for_status(); return BeautifulSoup(r.text,"html.parser")
def parse_generic(source):
 soup=get_soup(source["url"]); alerts=[]; seen=set()
 for a in soup.find_all("a",href=True):
  raw_title=clean_text(a); low=raw_title.lower()
  if len(raw_title)<20 or not any(k in low for k in source["keywords"]):continue
  href=urljoin(source["url"],a["href"])
  if href in seen or href.startswith("javascript:"):continue
  seen.add(href); title=clean_title(raw_title); context=clean_text(a.parent) if a.parent else title
  # Prefer metadata that belongs to the alert itself. Parent containers may contain several alerts.
  date=normalize_date(raw_title) or normalize_date(context)
  reference=extract_reference(raw_title) or extract_reference(context)
  alerts.append({"id":stable_id(source["agency"],title,href),"title":title,"agency":source["agency"],"category":source["category"],"date":date,"link":href,"description":title,"reference":reference,"risk":infer_risk(title),"severity":infer_severity(title,title),"status":"Publicada","lotes":extract_lots(raw_title),"barcodes":[]})
 return alerts
def load_existing():
 if not os.path.exists(DATA_FILE):return {}
 try:
  with open(DATA_FILE,encoding="utf-8") as f:raw=json.load(f)
  items=raw.get("alerts",[]) if isinstance(raw,dict) else raw
  return {x["id"]:x for x in items if isinstance(x,dict) and x.get("id")}
 except Exception:return {}
def main():
 os.makedirs(os.path.dirname(DATA_FILE),exist_ok=True); merged={}; source_status=[]
 # Rebuild from official sources on every run so corrected parsing does not preserve stale/bad records.
 for source in SOURCES:
  try:
   items=parse_generic(source)
   for item in items:merged[item["id"]]=item
   source_status.append({"agency":source["agency"],"category":source["category"],"url":source["url"],"ok":True,"items":len(items)})
   print(f"[{source['agency']} / {source['category']}] {len(items)} registros detectados")
  except Exception as exc:
   source_status.append({"agency":source["agency"],"category":source["category"],"url":source["url"],"ok":False,"error":str(exc)[:250]}); print(f"[{source['agency']} / {source['category']}] ERROR: {exc}")
 alerts=list(merged.values()); alerts.sort(key=lambda x:(x.get("date",""),x.get("title","")),reverse=True)
 payload={"meta":{"last_checked":datetime.now(timezone.utc).isoformat(),"sources":source_status,"count":len(alerts),"scope":"España","note":"Información agregada desde fuentes oficiales; verificar siempre la publicación original."},"alerts":alerts}
 with open(DATA_FILE,"w",encoding="utf-8") as f:json.dump(payload,f,ensure_ascii=False,indent=2)
 print(f"Registro actualizado: {len(alerts)} alertas")
if __name__=="__main__":main()
