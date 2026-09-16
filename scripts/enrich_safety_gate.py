import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "alertas.json"

# Clasificación secundaria. Solo actúa cuando el extractor no ha obtenido una
# categoría oficial reconocible. Nunca sustituye category_basis="official".
RULES = [
    ("Cosméticos", ("aftershave", "after shave", "perfume", "eau de", "cosmetic", "skin cream", "face cream", "body cream", "make-up", "makeup", "lipstick", "nail polish", "shampoo", "champu", "crema", "locion", "cosmetico")),
    ("Electrónica y aparatos eléctricos", ("radiator", "heater", "calefactor", "radiador", "charger", "adapter", "adaptor", "power adapter", "power supply", "transformer", "extension lead", "socket", "plug", "electric", "electrical", "battery", "usb", "cargador", "adaptador", "enchufe", "bateria")),
    ("Juguetes", ("toy", "doll", "soft toy", "plush", "slime", "puzzle", "play set", "playset", "piano play", "juguete", "muneca", "peluche")),
    ("Infantil", ("baby", "childcare", "stroller", "pushchair", "high chair", "cot ", "crib", "pacifier", "dummy", "bebe", "cochecito", "trona", "chupete")),
    ("Iluminación", ("lamp", "lighting", "light chain", "led light", "laser lighting", "luminaire", "lampara", "luminaria", "guirnalda")),
    ("Vehículos", ("motor vehicle", "car ", "motorcycle", "scooter", "tyre", "tire", "automovil", "vehiculo", "motocicleta", "patinete")),
    ("Deporte y ocio", ("e-bike", "ebike", "electric bicycle", "bicycle", "bike ", "fitness", "sports equipment", "skate", "bicicleta", "deporte")),
    ("Ropa y textiles", ("clothing", "dress", "shirt", "jacket", "shoe", "footwear", "textile", "ropa", "vestido", "camiseta", "chaqueta", "calzado")),
    ("Joyería", ("jewellery", "jewelry", "necklace", "bracelet", "earring", "ring ", "joyeria", "collar", "pulsera", "pendiente")),
    ("Productos químicos", ("chemical product", "glue", "adhesive", "detergent", "cleaner", "pegamento", "detergente", "limpiador")),
    ("Mobiliario", ("furniture", "chair", "table", "cabinet", "mueble", "silla", "mesa")),
    ("Maquinaria y herramientas", ("machine", "power tool", "drill", "grinder", "chainsaw", "circular saw", "maquina", "herramienta", "taladro", "sierra")),
    ("Equipos de protección", ("protective equipment", "respirator", "safety helmet", "life jacket", "proteccion")),
    ("Hogar y decoración", ("candle", "decoration", "decorative article", "household article", "vela", "decoracion")),
]


def plain(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(c for c in value if not unicodedata.combining(c)).lower()


def infer(alert):
    fields = [alert.get("product"), alert.get("title"), alert.get("description"), alert.get("official_category")]
    text = " ".join(plain(x) for x in fields if x)
    text = re.sub(r"\s+", " ", text)
    for category, terms in RULES:
        if any(term in text for term in terms):
            return category
    return None


def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    alerts = payload.get("alerts", [])
    before = Counter(a.get("category") for a in alerts if a.get("source_id") == "eu_safety_gate")
    changed = 0
    for alert in alerts:
        if alert.get("source_id") != "eu_safety_gate":
            continue
        # Los datos oficiales siempre prevalecen.
        if alert.get("category_basis") == "official":
            continue
        if alert.get("category") != "Otros productos":
            continue
        category = infer(alert)
        if category:
            alert["category"] = category
            alert["category_basis"] = "derived"
            alert["category_method"] = "text_fallback_v2"
            changed += 1

    after = Counter(a.get("category") for a in alerts if a.get("source_id") == "eu_safety_gate")
    payload.setdefault("meta", {})["category_enrichment"] = {
        "method": "text_fallback_v2",
        "changed": changed,
        "principle": "La categoría oficial prevalece; la inferencia solo se usa como respaldo cuando falta.",
    }
    DATA.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Safety Gate: categorías de respaldo mejoradas: {changed}")
    print(f"Otros productos: {before.get('Otros productos', 0)} -> {after.get('Otros productos', 0)}")


if __name__ == "__main__":
    main()
