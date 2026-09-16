"""Diagnóstico no destructivo y resiliente de Safety Gate.

Comprueba el índice público y analiza el texto de una ficha PDF oficial para
identificar qué campos pueden enriquecerse de forma trazable. No modifica datos.
"""
import io
import re
import time
from collections import Counter

import requests
from pypdf import PdfReader

API = "https://ec.europa.eu/safety-gate-alerts/public/api/notification/mostRecent/?"
PDF = "https://ec.europa.eu/safety-gate-alerts/api/download/notification/detail/pdf/{id}/es"
HEADERS = {
    "User-Agent": "ProductAlertSpain/4.3 (+https://github.com/progeekts/Product-Alert)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
}
LABELS = (
    "Categoría", "Categoría de producto", "Producto", "Nombre", "Marca", "Modelo",
    "Número de lote", "Lote", "Código de barras", "Barcode", "Riesgo", "Tipo de riesgo",
    "Descripción del riesgo", "Medidas", "Medidas adoptadas", "País notificante",
    "País de origen", "Países", "Reglamento", "Disposición legal", "Referencia",
)

def get_recent():
    for attempt in range(1, 4):
        try:
            r = requests.post(API, headers=HEADERS, json={"language": "es", "page": "0"}, timeout=45)
            print(f"mostRecent intento {attempt}/3 -> HTTP {r.status_code}")
            if r.ok:
                rows = r.json().get("content") or []
                if rows: return rows
            else: print(f"AVISO: Safety Gate respondió HTTP {r.status_code}")
        except Exception as exc: print(f"AVISO: intento {attempt} falló: {type(exc).__name__}: {exc}")
        if attempt < 3: time.sleep(attempt * 3)
    return []

def clean(text):
    text=text.replace("\u00a0"," "); text=re.sub(r"[ \t]+"," ",text); text=re.sub(r"\n{3,}","\n\n",text)
    return text.strip()

def inspect_pdf(notification_id):
    url=PDF.format(id=notification_id); r=requests.get(url,headers={"User-Agent":HEADERS["User-Agent"],"Accept-Language":HEADERS["Accept-Language"]},timeout=60)
    print(f"PDF id={notification_id} -> HTTP {r.status_code} · {r.headers.get('content-type','')} · {len(r.content)} bytes")
    if not r.ok or "pdf" not in r.headers.get("content-type","").lower(): return False
    try:
        reader=PdfReader(io.BytesIO(r.content)); text=clean("\n".join(page.extract_text() or "" for page in reader.pages))
    except Exception as exc:
        print(f"ERROR leyendo PDF: {type(exc).__name__}: {exc}"); return False
    print(f"Páginas: {len(reader.pages)} · texto extraído: {len(text)} caracteres")
    print("\n--- MUESTRA DE TEXTO EXTRAÍDO (máx. 8000 caracteres) ---"); print(text[:8000]); print("--- FIN MUESTRA ---")
    print("\nEtiquetas/campos detectables:"); lowered=text.casefold(); found=[]
    for label in LABELS:
        if label.casefold() in lowered: found.append(label); print(f"- {label}: sí")
    print(f"Total etiquetas detectadas: {len(found)}/{len(LABELS)}"); return bool(text)

def main():
    rows=get_recent()
    if not rows:
        print("RESULTADO: índice oficial no disponible; diagnóstico controlado sin modificar producción."); return
    keys=Counter(k for row in rows for k in row); print(f"Filas analizadas: {len(rows)}"); print("Campos raíz del resumen:",", ".join(sorted(keys)))
    tested=0
    for row in rows[:5]:
        notification_id=row.get("id")
        if notification_id and inspect_pdf(notification_id): tested+=1
        if tested>=2: break
    print(f"\nRESULTADO: {tested} fichas PDF con texto extraíble analizadas.")
    if not tested: print("AVISO: no se encontró una ficha PDF con texto extraíble en la muestra.")
if __name__=="__main__": main()
