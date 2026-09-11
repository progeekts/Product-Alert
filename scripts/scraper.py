import json
import os
import re
import hashlib
from datetime import datetime
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "alertas.json")

# Fuentes públicas de alertas de consumo en España
FEEDS = [
    {
        "agency": "AESAN",
        "category": "alimentacion",
        "url": "https://www.aesan.gob.es/AECOSAN/web/rss/seguridad_alimentaria.xml"
    },
    {
        "agency": "AEMPS",
        "category": "medicamentos",
        "url": "https://www.aemps.gob.es/categoria/medicamentos-de-uso-humano/defectos-de-calidad/feed/"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9"
}

def generate_id(cadena: str) -> str:
    return hashlib.sha256(cadena.encode("utf-8")).hexdigest()[:16]

def extract_patterns(text: str):
    """Extrae heurísticamente lotes y códigos de barras (EAN-13/UPC)."""
    lotes = []
    barcodes = []

    # Extraer lotes (ej: Lote 123, L-9874, Batch: ABC)
    matches_lote = re.findall(r"(?:lote|n[ºo]\s*de\s*lote|batch)[:\s]+([A-Za-z0-9\-_/]+)", text, re.IGNORECASE)
    if matches_lote:
        lotes = list(dict.fromkeys(matches_lote))

    # Extraer números EAN (8 a 13 dígitos independientes)
    matches_barcode = re.findall(r"\b\d{8,14}\b", text)
    if matches_barcode:
        barcodes = list(dict.fromkeys(matches_barcode))

    return lotes, barcodes

def fetch_feed(feed_cfg):
    alerts = []
    try:
        res = requests.get(feed_cfg["url"], headers=HEADERS, timeout=25)
        if res.status_code != 200:
            print(f"[{feed_cfg['agency']}] Respuesta HTTP {res.status_code}. Omitiendo.")
            return alerts

        root = ET.fromstring(res.content)
        # Soporta tanto RSS 2.0 (<item>) como Atom (<entry>)
        items = root.findall(".//item")
        if not items:
            items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items:
            title = (item.findtext("title") or item.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
            link = (item.findtext("link") or item.findtext("{http://www.w3.org/2005/Atom}link") or "").strip()
            pub_date = (item.findtext("pubDate") or item.findtext("{http://www.w3.org/2005/Atom}updated") or "").strip()
            raw_desc = (item.findtext("description") or item.findtext("{http://www.w3.org/2005/Atom}summary") or "").strip()

            clean_desc = BeautifulSoup(raw_desc, "html.parser").get_text(separator=" ").strip()
            full_text = f"{title} {clean_desc}"
            lotes, barcodes = extract_patterns(full_text)

            if title:
                alerts.append({
                    "id": generate_id(link or title),
                    "title": title,
                    "agency": feed_cfg["agency"],
                    "category": feed_cfg["category"],
                    "date": pub_date[:10] if len(pub_date) >= 10 else datetime.utcnow().strftime("%Y-%m-%d"),
                    "link": link,
                    "description": clean_desc,
                    "lotes": lotes,
                    "barcodes": barcodes
                })
    except Exception as err:
        print(f"[{feed_cfg['agency']}] Error de conexión o parseo: {err}")

    return alerts

def main():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    existing_map = {}

    # 1. Cargar datos preexistentes para no sobreescribir si un feed falla temporalmente
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                existing_map = {entry["id"]: entry for entry in data if "id" in entry}
        except Exception:
            existing_map = {}

    # 2. Descargar y actualizar
    for feed in FEEDS:
        new_entries = fetch_feed(feed)
        for entry in new_entries:
            existing_map[entry["id"]] = entry

    # 3. Guardar archivo unificado
    consolidated = list(existing_map.values())
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, ensure_ascii=False, indent=2)
    print(f"data/alertas.json actualizado correctamente. Total registros: {len(consolidated)}")

if __name__ == "__main__":
    main()
