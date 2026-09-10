import json
import os
import re
import hashlib
from datetime import datetime
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "alertas.json")

# Fuentes públicas de ejemplo con estructura RSS o feeds XML estándar
FEEDS = [
    {
        "agency": "AESAN",
        "category": "alimentacion",
        "url": "https://www.aesan.gob.es/AECOSAN/web/rss/seguridad_alimentaria.xml"
    }
]

def generate_id(cadena: str) -> str:
    return hashlib.sha256(cadena.encode("utf-8")).hexdigest()[:16]

def extract_patterns(text: str):
    """Extrae posibles lotes y códigos de barras del texto de la alerta."""
    lotes = []
    barcodes = []

    # Detección heurística de lotes (ej: Lote: 1234, L-12345)
    lote_matches = re.findall(r"(?:lote|lote n[ºo]|batch)[:\s]+([A-Za-z0-9\-_]+)", text, re.IGNORECASE)
    if lote_matches:
        lotes = list(set(lote_matches))

    # Detección de EAN-13 o UPC (8 a 14 dígitos numéricos)
    barcode_matches = re.findall(r"\b\d{8,14}\b", text)
    if barcode_matches:
        barcodes = list(set(barcode_matches))

    return lotes, barcodes

def fetch_feed(feed_config):
    alerts = []
    headers = {"User-Agent": "Mozilla/5.0 (GitHubAction-ConsumerAlertsTracker/1.0)"}

    try:
        response = requests.get(feed_config["url"], headers=headers, timeout=20)
        if response.status_code != 200:
            return alerts

        root = ET.fromstring(response.content)
        items = root.findall(".//item")

        for item in items:
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()
            description = item.findtext("description", default="").strip()

            # Limpiar etiquetas HTML de la descripción
            soup = BeautifulSoup(description, "html.parser")
            clean_desc = soup.get_text(separator=" ").strip()

            full_text = f"{title} {clean_desc}"
            lotes, barcodes = extract_patterns(full_text)

            alert_id = generate_id(link or title)

            alerts.append({
                "id": alert_id,
                "title": title,
                "agency": feed_config["agency"],
                "category": feed_config["category"],
                "date": pub_date or datetime.utcnow().strftime("%Y-%m-%d"),
                "link": link,
                "description": clean_desc,
                "lotes": lotes,
                "barcodes": barcodes
            })
    except Exception as exc:
        print(f"Error procesando {feed_config['agency']}: {exc}")

    return alerts

def main():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    
    existing_alerts = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
                existing_alerts = {item["id"]: item for item in records}
        except Exception:
            existing_alerts = {}

    # Recolectar nuevos avisos
    for feed in FEEDS:
        items = fetch_feed(feed)
        for item in items:
            # Upsert: conservar si ya existe o agregar si es nuevo
            existing_alerts[item["id"]] = item

    # Guardar ordenado de forma cronológica inversa
    consolidated = list(existing_alerts.values())
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()