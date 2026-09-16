import json
import os
import hashlib
from datetime import datetime, timezone

import requests

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_FILE = os.path.join(ROOT, "data", "alertas.json")
API = "https://ec.europa.eu/safety-gate-alerts/public/api/notification/mostRecent/?"
DETAIL = "https://ec.europa.eu/safety-gate-alerts/screen/webReport/alertDetail/{}"
IMAGE = "https://ec.europa.eu/safety-gate-alerts/public/api/notification/image/{}"
HEADERS = {
    "User-Agent": "ProductAlertSpain/3.0 (+https://github.com/progeekts/Product-Alert)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
}
PAGES = 4

CATEGORY_ES = {
    "TOYS": "Juguetes",
    "ELECTRICAL_APPLIANCES": "Electrónica y aparatos eléctricos",
    "MOTOR_VEHICLES": "Vehículos",
    "COSMETICS": "Cosméticos",
    "CLOTHING_TEXTILES_AND_FASHION_ITEMS": "Ropa y textiles",
    "CHILDCARE_ARTICLES_AND_CHILDRENS_EQUIPMENT": "Infantil",
    "CHEMICAL_PRODUCTS": "Productos químicos",
    "MACHINERY": "Maquinaria y herramientas",
    "FURNITURE": "Mobiliario",
    "SPORTS_EQUIPMENT": "Deporte y ocio",
    "JEWELLERY": "Joyería",
    "LASER_POINTERS": "Láser",
    "LIGHTING_CHAINS": "Iluminación",
}

RISK_ES = {
    "CHEMICAL": "Riesgo químico",
    "CHOKING": "Asfixia",
    "INJURIES": "Lesiones",
    "ELECTRIC_SHOCK": "Descarga eléctrica",
    "FIRE": "Incendio",
    "BURNS": "Quemaduras",
    "STRANGULATION": "Estrangulamiento",
    "SUFFOCATION": "Asfixia",
    "DROWNING": "Ahogamiento",
    "MICROBIOLOGICAL": "Riesgo microbiológico",
    "ENVIRONMENT": "Riesgo medioambiental",
    "DAMAGE_TO_SIGHT": "Daño ocular",
    "HEARING_DAMAGE": "Daño auditivo",
}


def stable_id(reference, notification_id):
    return hashlib.sha256(f"SAFETY_GATE|{reference}|{notification_id}".encode()).hexdigest()[:20]


def first_version(obj, language="ES"):
    versions = obj.get("versions") or []
    for version in versions:
        if (version.get("language") or {}).get("key") == language:
            return version
    for version in versions:
        if (version.get("language") or {}).get("key") == "EN":
            return version
    return versions[0] if versions else {}


def names(items, key="name"):
    result = []
    for item in items or []:
        if isinstance(item, dict):
            value = item.get(key)
            if value:
                result.append(value)
    return list(dict.fromkeys(result))


def iso_date(value):
    return (value or "")[:10]


def severity(row):
    code = ((row.get("notificationType") or {}).get("code") or "").upper()
    if code in {"A12", "SR"}:
        return "alta"
    return "media"


def normalize(row):
    notification_id = row.get("id")
    reference = row.get("reference") or ""
    product = row.get("product") or {}
    product_version = first_version(product)
    risk = row.get("risk") or {}
    risk_version = first_version(risk)
    trace = row.get("traceability") or {}
    measure_taken = row.get("measureTaken") or {}

    category_key = ((product.get("productCategory") or {}).get("name") or "").upper()
    category = CATEGORY_ES.get(category_key, category_key.replace("_", " ").title() or "Otros productos")
    product_name = product.get("nameSpecific") or product_version.get("name") or product.get("name") or "Producto sin nombre publicado"
    brands = [x.get("brand") for x in product.get("brands") or [] if isinstance(x, dict) and x.get("brand")]
    models = [x.get("modelType") for x in product.get("modelTypes") or [] if isinstance(x, dict) and x.get("modelType")]
    barcodes = [x.get("barcode") for x in product.get("barcodes") or [] if isinstance(x, dict) and x.get("barcode")]
    lots = [x.get("batchNumber") for x in product.get("batchNumbers") or [] if isinstance(x, dict) and x.get("batchNumber")]
    risk_codes = names(risk.get("riskType") or [])
    risk_labels = [RISK_ES.get(x, x.replace("_", " ").title()) for x in risk_codes]
    measures = []
    for measure in measure_taken.get("measures") or []:
        cat = (measure.get("measureCategory") or {}).get("name")
        typ = (measure.get("measureType") or {}).get("name")
        if cat:
            measures.append({
                "category": cat,
                "type": typ or "",
                "date": iso_date(measure.get("entryIntoForceDate")),
            })

    notifying = row.get("country") or {}
    reacting = [((x.get("country") or {}).get("key")) for x in row.get("reactingCountries") or []]
    reacting = [x for x in reacting if x]
    spain_confirmed = notifying.get("key") == "ES" or "ES" in reacting
    photos = product.get("photos") or []
    main_photo = next((p for p in photos if p.get("mainPicture")), photos[0] if photos else None)
    image = IMAGE.format(main_photo.get("id")) if main_photo and main_photo.get("id") else ""
    risk_description = risk_version.get("riskDescription") or ""
    legal = risk_version.get("legalProvision") or ""
    description = product_version.get("description") or product_name

    title_parts = [product_name]
    if brands:
        title_parts.append(" · " + ", ".join(brands[:2]))
    if reference:
        title_parts.append(f" ({reference})")

    return {
        "id": stable_id(reference, notification_id),
        "source_id": "eu_safety_gate",
        "title": "".join(title_parts),
        "agency": "Safety Gate UE",
        "category": category,
        "date": iso_date(row.get("publicationDate") or row.get("modificationDate")),
        "link": DETAIL.format(notification_id),
        "description": risk_description or description,
        "reference": reference,
        "risk": ", ".join(risk_labels),
        "severity": severity(row),
        "status": "Publicada",
        "product": product_name,
        "brands": brands,
        "models": models,
        "lotes": lots,
        "barcodes": barcodes,
        "measures": measures,
        "consumer_action": "Consulta las medidas oficiales de la alerta. La presencia en Safety Gate no implica por sí sola que el producto se haya comercializado en España.",
        "legal_provision": legal,
        "notifying_country": notifying.get("name") or "",
        "country_origin": (trace.get("countryOrigin") or {}).get("name") or "",
        "sold_online": (trace.get("isSoldOnline") or {}).get("name") or "",
        "reacting_countries": reacting,
        "geographic_scope": "UE/EEE",
        "spain_confirmed": spain_confirmed,
        "image": image,
        "official_data": True,
    }


def fetch_recent():
    alerts = []
    total_pages = None
    for page in range(PAGES):
        response = requests.post(API, headers=HEADERS, json={"language": "es", "page": str(page)}, timeout=45)
        response.raise_for_status()
        data = response.json()
        if total_pages is None:
            total_pages = data.get("totalPages")
        content = data.get("content") or []
        if not content:
            break
        alerts.extend(normalize(row) for row in content if row.get("id"))
        if isinstance(total_pages, int) and page + 1 >= total_pages:
            break
    if not alerts:
        raise RuntimeError("Safety Gate devolvió cero alertas; se evita sobrescribir el último conjunto conocido")
    return alerts


def main():
    with open(DATA_FILE, encoding="utf-8") as handle:
        payload = json.load(handle)
    previous = payload.get("alerts", [])
    old_safety = [x for x in previous if x.get("source_id") == "eu_safety_gate"]
    base = [x for x in previous if x.get("source_id") != "eu_safety_gate"]
    checked = datetime.now(timezone.utc).isoformat()
    sources = [x for x in payload.get("meta", {}).get("sources", []) if x.get("id") != "eu_safety_gate"]
    try:
        current = fetch_recent()
        by_ref = {x.get("reference") or x.get("id"): x for x in old_safety}
        for item in current:
            by_ref[item.get("reference") or item.get("id")] = item
        safety = list(by_ref.values())
        sources.append({
            "id": "eu_safety_gate",
            "agency": "Comisión Europea",
            "category": "Productos no alimentarios",
            "url": "https://ec.europa.eu/safety-gate-alerts/screen/search",
            "ok": True,
            "stale": False,
            "items": len(safety),
            "fetched_now": len(current),
            "checked_at": checked,
            "last_success": checked,
        })
        print(f"[eu_safety_gate] {len(current)} alertas recientes; histórico local Safety Gate: {len(safety)}")
    except Exception as exc:
        safety = old_safety
        old = next((x for x in payload.get("meta", {}).get("sources", []) if x.get("id") == "eu_safety_gate"), {})
        sources.append({
            "id": "eu_safety_gate",
            "agency": "Comisión Europea",
            "category": "Productos no alimentarios",
            "url": "https://ec.europa.eu/safety-gate-alerts/screen/search",
            "ok": False,
            "stale": True,
            "items": len(safety),
            "checked_at": checked,
            "last_success": old.get("last_success"),
            "error": str(exc)[:250],
        })
        print(f"[eu_safety_gate] ERROR; se conservan {len(safety)} alertas previas: {exc}")

    alerts = base + safety
    alerts.sort(key=lambda x: (x.get("date", ""), x.get("title", "")), reverse=True)
    payload.setdefault("meta", {})["sources"] = sources
    payload["meta"]["count"] = len(alerts)
    payload["meta"]["last_checked"] = checked
    payload["meta"]["version"] = 7
    payload["meta"]["scope"] = "España + alertas UE/EEE claramente identificadas"
    payload["meta"]["note"] = "Fuentes oficiales españolas más Safety Gate de la Comisión Europea. Las alertas Safety Gate se etiquetan como UE/EEE y no se presentan como comercializadas en España salvo que la fuente lo confirme."
    payload["alerts"] = alerts
    with open(DATA_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"Registro combinado actualizado: {len(alerts)} alertas")


if __name__ == "__main__":
    main()
