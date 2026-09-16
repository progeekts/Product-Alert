"""Enriquece alertas Safety Gate usando sus fichas PDF oficiales.

Extracción conservadora: solo acepta campos delimitados por encabezados observados.
Si un límite no puede identificarse, el campo se omite en vez de contaminar datos.
"""
import io, json, os, re, time
from datetime import datetime, timezone
import requests
from pypdf import PdfReader

ROOT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..")); DATA_FILE=os.path.join(ROOT,"data","alertas.json")
PDF="https://ec.europa.eu/safety-gate-alerts/api/download/notification/detail/pdf/{id}/es"
HEADERS={"User-Agent":"ProductAlertSpain/4.7 (+https://github.com/progeekts/Product-Alert)","Accept-Language":"es-ES,es;q=0.9,en;q=0.5"}
MAX_PER_RUN=35; PARSER_VERSION=3
LABELS=["Número de aviso","País notificante","Categoría del producto","Tipo","Producto","Nombre","Descripción del embalaje","Marca","Tipo / número de modelo","Número de lote","Código de barras","Descripción del producto","Tipo de riesgo","Descripción del riesgo","País de origen","Medidas adoptadas por los agentes económicos","Medidas ordenadas por las autoridades públicas","Fecha de entrada en vigor","Comerciante en línea","Productos encontrados y medidas adoptadas también en"]
CATEGORY_MAP={"ropa, textiles y artículos de moda":"Ropa y textiles","aparatos y equipos eléctricos":"Electrónica y aparatos eléctricos","juguetes":"Juguetes","cosméticos":"Cosméticos","vehículos a motor":"Vehículos","productos químicos":"Productos químicos","artículos de puericultura y equipos para niños":"Infantil","maquinaria":"Maquinaria y herramientas","muebles":"Mobiliario","joyería":"Joyería","equipos de protección":"Equipos de protección"}

def clean(text):
    text=text.replace("\u00a0"," ").replace("\r",""); text=re.sub(r"[ \t]+"," ",text); text=re.sub(r"\n(?:\d{2}/\d{2}/\d{4} )?Página \d+\n","\n",text)
    return re.sub(r"\n{3,}","\n\n",text).strip()

def _positions(tail,labels):
    pos=[]
    for label in labels:
        m=re.search(r"\n"+re.escape(label)+r"(?:\s|\n)",tail,re.I)
        if m: pos.append(m.start())
    m=re.search(r"\nDisposiciones jurídicas\s*\(a(?:\s|\n)*nivel de la UE\)",tail,re.I)
    if m: pos.append(m.start())
    return pos

def trim_section(value):
    if not value: return ""
    markers=[r"\s+Disposiciones jurídicas\s*\(a",r"\s+País de origen\b",r"\s+Medidas adoptadas por los agentes económicos\b",r"\s+Medidas ordenadas por las autoridades públicas\b",r"\s+Comerciante en línea\b",r"\s+Productos encontrados y medidas adoptadas también en\b"]
    ends=[]
    for marker in markers:
        m=re.search(marker,value,re.I)
        if m: ends.append(m.start())
    return value[:min(ends)].strip(" :-") if ends else value.strip(" :-")

def field(text,label):
    start=re.search(r"(?:^|\n)"+re.escape(label)+r"\s+",text,re.I)
    if not start: return ""
    tail=text[start.end():]; pos=_positions(tail,[x for x in LABELS if x.casefold()!=label.casefold()])
    if not pos: return ""
    return trim_section(re.sub(r"\s*\n\s*"," ",tail[:min(pos)]))

def legal_field(text):
    marker=re.search(r"Disposiciones jurídicas\s*\(a(?:\s|\n)*nivel de la UE\).*?incumplimiento\s*\n",text,re.I|re.S)
    if not marker: return ""
    tail=text[marker.end():]; pos=_positions(tail,["País de origen","Medidas adoptadas por los agentes económicos","Medidas ordenadas por las autoridades públicas","Fecha de entrada en vigor","Comerciante en línea","Productos encontrados y medidas adoptadas también en"])
    if not pos: return ""
    return trim_section(re.sub(r"\s*\n\s*"," ",tail[:min(pos)]))

def pdf_text(nid):
    r=requests.get(PDF.format(id=nid),headers=HEADERS,timeout=60); r.raise_for_status()
    if "pdf" not in r.headers.get("content-type","").lower(): raise ValueError("la respuesta no es PDF")
    return clean("\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(r.content)).pages))

def notification_id(item):
    m=re.search(r"alertDetail/(\d+)",item.get("link") or ""); return m.group(1) if m else ""

def sane(value):
    bad=("Medidas adoptadas","Medidas ordenadas","Comerciante en línea","Página ","Disposiciones jurídicas")
    return bool(value) and not any(x.casefold() in value.casefold() for x in bad)

def enrich(item,text):
    old_pdf=bool(item.get("pdf_detail_enriched"))
    official_category=field(text,"Categoría del producto"); product=field(text,"Producto"); brand=field(text,"Marca"); model=field(text,"Tipo / número de modelo"); lot=field(text,"Número de lote"); barcode=field(text,"Código de barras"); description=field(text,"Descripción del producto"); risk_type=field(text,"Tipo de riesgo"); risk_description=field(text,"Descripción del riesgo"); notifying=field(text,"País notificante"); origin=field(text,"País de origen"); economic=field(text,"Medidas adoptadas por los agentes económicos"); authority=field(text,"Medidas ordenadas por las autoridades públicas"); legal=legal_field(text)
    if sane(official_category): item.update(official_category=official_category,category=CATEGORY_MAP.get(official_category.casefold(),official_category),category_basis="official",category_method="safety_gate_pdf")
    if sane(product): item["product"]=product
    if sane(brand) and brand.casefold()!="desconocido": item["brands"]=[brand]
    if sane(model): item["models"]=[model]
    if sane(lot): item["lotes"]=[lot]
    if sane(barcode): item["barcodes"]=[barcode]
    if sane(risk_type): item["risk"]=risk_type
    if sane(risk_description): item["description"]=risk_description; item["risk_description"]=risk_description
    elif sane(description): item["description"]=description; item["risk_description"]=""
    elif old_pdf and "Disposiciones jurídicas" in (item.get("risk_description") or ""): item["risk_description"]=""
    if sane(notifying): item["notifying_country"]=notifying
    if sane(origin): item["country_origin"]=origin
    elif old_pdf: item["country_origin"]=""
    if sane(legal): item["legal_provision"]=legal
    elif old_pdf: item["legal_provision"]=""
    measures=[]
    if sane(economic): measures.append({"category":"Agentes económicos","type":economic,"date":""})
    if sane(authority): measures.append({"category":"Autoridades públicas","type":authority,"date":""})
    if measures or old_pdf: item["measures"]=measures
    item["consumer_action"]="Consulta la ficha oficial de Safety Gate y las indicaciones de las autoridades o del vendedor. La alerta no demuestra por sí sola que el producto se haya comercializado en España."
    item.update(pdf_detail_enriched=True,pdf_detail_parser_version=PARSER_VERSION,pdf_detail_source=PDF.format(id=notification_id(item)),pdf_detail_language="es (traducción automática de Safety Gate; prevalece la versión inglesa en caso de discrepancia)",pdf_detail_enriched_at=datetime.now(timezone.utc).isoformat())

def main():
    with open(DATA_FILE,encoding="utf-8") as h: payload=json.load(h)
    candidates=[x for x in payload.get("alerts",[]) if x.get("source_id")=="eu_safety_gate" and x.get("pdf_detail_parser_version")!=PARSER_VERSION]
    ok=failed=0
    for item in candidates[:MAX_PER_RUN]:
        nid=notification_id(item)
        if not nid: continue
        try:
            text=pdf_text(nid)
            if not text or "Safety Gate Alerts" not in text: raise ValueError("texto oficial no reconocible")
            enrich(item,text); ok+=1
        except Exception as exc: failed+=1; print(f"[safety_gate_pdf] {nid}: {type(exc).__name__}: {exc}")
        time.sleep(.15)
    payload.setdefault("meta",{})["safety_gate_pdf_enrichment"]={"enabled":True,"source":"official_pdf","parser_version":PARSER_VERSION,"processed_now":ok,"failed_now":failed,"remaining":max(0,len(candidates)-ok),"checked_at":datetime.now(timezone.utc).isoformat(),"note":"Enriquecimiento progresivo desde fichas PDF oficiales; extracción delimitada y fallos sin pérdida de historial."}
    with open(DATA_FILE,"w",encoding="utf-8") as h: json.dump(payload,h,ensure_ascii=False,indent=2); h.write("\n")
    print(f"Safety Gate PDF v{PARSER_VERSION}: {ok} enriquecidas/reprocesadas, {failed} fallos, {max(0,len(candidates)-ok)} pendientes")
if __name__=="__main__": main()
