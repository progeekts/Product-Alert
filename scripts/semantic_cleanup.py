import json
import os
import unicodedata

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_FILE = os.path.join(ROOT, "data", "alertas.json")


def canonical(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(c for c in text if not unicodedata.combining(c)).strip().lower()


def main():
    with open(DATA_FILE, encoding="utf-8") as handle:
        payload = json.load(handle)

    changed = 0
    for alert in payload.get("alerts", []):
        if alert.get("source_id") != "eu_safety_gate":
            continue

        notifying = canonical(alert.get("notifying_country"))
        reacting = {str(x).upper() for x in alert.get("reacting_countries") or []}
        notified_by_spain = notifying in {"espana", "spain", "es"}
        spain_follow_up = "ES" in reacting

        alert["notified_by_spain"] = notified_by_spain
        alert["spain_follow_up"] = spain_follow_up
        alert["spain_related"] = notified_by_spain or spain_follow_up
        # Compatibilidad temporal: deja de significar «comercializado en España».
        alert["spain_confirmed"] = False
        alert["consumer_action"] = (
            "Consulta la publicación oficial y las medidas indicadas para este producto. "
            "Que una alerta figure en Safety Gate, o que España haya realizado un seguimiento, "
            "no demuestra por sí solo que el producto se haya comercializado en España."
        )
        changed += 1

    meta = payload.setdefault("meta", {})
    meta["version"] = max(int(meta.get("version") or 0), 9)
    meta["note"] = (
        "Fuentes oficiales españolas y Safety Gate. En Safety Gate se distingue entre país "
        "notificante y países con actuaciones de seguimiento; ninguna de esas señales se "
        "interpreta automáticamente como prueba de comercialización en España."
    )

    with open(DATA_FILE, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    print(f"Semántica geográfica normalizada en {changed} alertas Safety Gate")


if __name__ == "__main__":
    main()
