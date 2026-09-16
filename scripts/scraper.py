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

HEADERS = {
    "User-Agent": "ProductAlertSpain/1.0 (+https://github.com/progeekts/Product-Alert)",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
}

SOURCES = [
    {
        "agency": "AESAN",
        "category": "Alimentación",
        "kind": "html",
        "url": "https://www.aesan.gob.es/alertas/alertas-alimentarias",
        "parser": "aesan",
    },
    {
        "agency": "AEMPS",
        "category": "Productos sanitarios",
        "kind": "html",
        "url": "https://www.aemps.gob.es/productos-sanitarios/acciones-informativas-productos-sanitarios/",
        "parser": "aemps_ps",
    },
    {
        "agency": "AEMPS",
        "category": "Medicamentos",
        "kind": "html",
        "url": "https://www.aemps.gob.es/comunicacion/alertas/alertas-farmaceuticas-y-retiradas-de-lotes-de-medicamentos-de-uso-humano-por-defectos-de-calidad/",
        "parser": "aemps_med",
    },
]

DATE_PATTERNS = ["%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%Y-%m-%d"]
MONTHS_ES = {
    "enero": "01", "febrero": "02", "marzo": "03", "abril": "04",
    "mayo": "05", "junio": "06", "julio": "07", "agosto": "08",
    "septiembre": "09", "setiembre": "09", "octubre": "10",
    "noviembre": "11", "diciembre": "12"
}


def stable_id(agency, title, link):
    raw = f"{agency}|{title}|{link}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:20]


def normalize_date(text):
    if not text:
        return ""
    t = " ".join(text.split()).strip()
    m = re.search(r"(\d{1,2})\s+([A-Za-zÁÉÍÓÚáéíóúñÑ]+)\s+(20\d{2})", t)
    if m:
        month = MONTHS_ES.get(m.group(2).lower())
        if month:
            return f"{m.group(3)}-{month}-{int(m.group(1)):02d}"
    m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](20\d{2})", t)
    if m:
        return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.search(r"(20\d{2})-(\d{2})-(\d{2})", t)
    return m.group(0) if m else ""


def extract_reference(text):
    patterns = [
        r"Ref\.?\s*[:.]?\s*([A-Z]{1,4}\s*20\d{2}/\d+)",
        r"\b(ES20\d{2}/\d+)\b",
        r"\b(PS,?\s*\d+/20\d{2})\b",
        r"\b(\d{1,4}/20\d{2})\b",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
    return ""


def extract_lots(text):
    found = re.findall(r"(?:lote|lotes|n[ºo]\.?\s*de\s*lote)\s*[:\-]?\s*([A-Z0-9][A-Z0-9._/-]{2,})", text, re.I)
    return list(dict.fromkeys(x.rstrip(".,;) ") for x in found))[:12]


def infer_severity(title, description):
    t = f"{title} {description}".lower()
    high = ["salmonella", "listeria", "vidrio", "cuerpos extraños", "asfixia", "riesgo grave", "retirada del mercado", "retirada de lotes", "suspensión de la administración"]
    medium = ["alérgeno", "gluten", "leche no declarada", "fallo", "defecto", "advertencia", "riesgo"]
    if any(x in t for x in high):
        return "alta"
    if any(x in t for x in medium):
        return "media"
    return "informativa"


def infer_risk(title):
    t = title.lower()
    mapping = [
        ("salmonella", "Salmonella"), ("listeria", "Listeria"), ("gluten", "Alérgeno / gluten"),
        ("leche", "Alérgeno / leche"), ("mostaza", "Alérgeno / mostaza"), ("vidrio", "Cuerpos extraños"),
        ("defecto", "Defecto de calidad"), ("fallo", "Fallo de producto"), ("retirada", "Retirada")
    ]
    for needle, label in mapping:
        if needle in t:
            return label
    return ""


def clean_text(node):
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


def get_soup(url):
    r = requests.get(url, headers=HEADERS, timeout=35)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def parse_aesan(source):
    soup = get_soup(source["url"])
    alerts = []
    seen = set()
    for a in soup.find_all("a", href=True):
        title = clean_text(a)
        if len(title) < 25:
            continue
        low = title.lower()
        if not any(k in low for k in ["alerta", "advertencia", "ampliación"]):
            continue
        href = urljoin(source["url"], a["href"])
        if href in seen:
            continue
        seen.add(href)
        parent_text = clean_text(a.parent) if a.parent else title
        date = normalize_date(parent_text)
        alerts.append({
            "id": stable_id(source["agency"], title, href),
            "title": title,
            "agency": source["agency"],
            "category": source["category"],
            "date": date,
            "link": href,
            "description": title,
            "reference": extract_reference(title),
            "risk": infer_risk(title),
            "severity": infer_severity(title, title),
            "status": "Publicada",
            "lotes": extract_lots(title),
            "barcodes": [],
        })
    return alerts


def parse_aemps_ps(source):
    soup = get_soup(source["url"])
    alerts = []
    seen = set()
    for a in soup.find_all("a", href=True):
        title = clean_text(a)
        low = title.lower()
        if len(title) < 30 or not any(k in low for k in ["aemps informa", "retirada", "riesgo", "fallo", "defecto"]):
            continue
        href = urljoin(source["url"], a["href"])
        if href in seen:
            continue
        seen.add(href)
        context = clean_text(a.parent) if a.parent else title
        alerts.append({
            "id": stable_id(source["agency"], title, href),
            "title": title,
            "agency": source["agency"],
            "category": source["category"],
            "date": normalize_date(context),
            "link": href,
            "description": title,
            "reference": extract_reference(context),
            "risk": infer_risk(title),
            "severity": infer_severity(title, title),
            "status": "Publicada",
            "lotes": extract_lots(title),
            "barcodes": [],
        })
    return alerts


def parse_aemps_med(source):
    soup = get_soup(source["url"])
    alerts = []
    seen = set()
    # The AEMPS page is an index of pharmaceutical quality alerts. Keep links whose text clearly identifies an alert/withdrawal.
    for a in soup.find_all("a", href=True):
        title = clean_text(a)
        low = title.lower()
        if len(title) < 20 or not any(k in low for k in ["alerta", "retirada", "defecto de calidad"]):
            continue
        href = urljoin(source["url"], a["href"])
        if href in seen or "javascript:" in href:
            continue
        seen.add(href)
        context = clean_text(a.parent) if a.parent else title
        alerts.append({
            "id": stable_id(source["agency"], title, href),
            "title": title,
            "agency": source["agency"],
            "category": source["category"],
            "date": normalize_date(context),
            "link": href,
            "description": title,
            "reference": extract_reference(context),
            "risk": "Defecto de calidad" if "defecto" in low else "Retirada" if "retirada" in low else "",
            "severity": infer_severity(title, title),
            "status": "Publicada",
            "lotes": extract_lots(context),
            "barcodes": [],
        })
    return alerts


PARSERS = {"aesan": parse_aesan, "aemps_ps": parse_aemps_ps, "aemps_med": parse_aemps_med}


def load_existing():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            raw = json.load(f)
        items = raw.get("alerts", []) if isinstance(raw, dict) else raw
        return {x["id"]: x for x in items if isinstance(x, dict) and x.get("id")}
    except Exception:
        return {}


def main():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    merged = load_existing()
    source_status = []
    for source in SOURCES:
        try:
            items = PARSERS[source["parser"]](source)
            for item in items:
                merged[item["id"]] = item
            source_status.append({"agency": source["agency"], "url": source["url"], "ok": True, "items": len(items)})
            print(f"[{source['agency']}] {len(items)} registros detectados")
        except Exception as exc:
            source_status.append({"agency": source["agency"], "url": source["url"], "ok": False, "error": str(exc)[:250]})
            print(f"[{source['agency']}] ERROR: {exc}")

    alerts = list(merged.values())
    alerts.sort(key=lambda x: (x.get("date", ""), x.get("title", "")), reverse=True)
    payload = {
        "meta": {
            "last_checked": datetime.now(timezone.utc).isoformat(),
            "sources": source_status,
            "count": len(alerts),
            "scope": "España",
            "note": "Información agregada desde fuentes oficiales; verificar siempre la publicación original."
        },
        "alerts": alerts
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"Registro actualizado: {len(alerts)} alertas")


if __name__ == "__main__":
    main()
