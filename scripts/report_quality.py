import json
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "alertas.json"
payload = json.loads(DATA.read_text(encoding="utf-8"))
alerts = payload.get("alerts", [])
safety = [a for a in alerts if a.get("source_id") == "eu_safety_gate"]

print("PRODUCT ALERT · INFORME DE CALIDAD")
print("=" * 38)
print("Total:", len(alerts))
print("España/fuentes nacionales:", len([a for a in alerts if a.get("source_id") != "eu_safety_gate"]))
print("Safety Gate:", len(safety))
print("Safety Gate notificadas por España:", len([a for a in safety if a.get("notified_by_spain") is True]))
print("Safety Gate con seguimiento de España:", len([a for a in safety if a.get("spain_follow_up") is True]))
print("Safety Gate con relación administrativa con España:", len([a for a in safety if a.get("spain_related") is True]))
print("Safety Gate con categoría oficial:", len([a for a in safety if a.get("category_basis") == "official"]))
print("Safety Gate con categoría derivada:", len([a for a in safety if a.get("category_basis") == "derived"]))
print("Safety Gate en Otros productos:", len([a for a in safety if a.get("category") == "Otros productos"]))
print("Con imagen oficial:", len([a for a in alerts if a.get("image")]))
print("Con marca:", len([a for a in alerts if a.get("brands")]))
print("Con lote:", len([a for a in alerts if a.get("lotes")]))
print("\nCategorías:")
for category, count in Counter(a.get("category") or "Sin categoría" for a in alerts).most_common():
    print(f"- {category}: {count}")
