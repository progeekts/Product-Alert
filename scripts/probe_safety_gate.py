"""Diagnóstico no destructivo de la estructura pública de Safety Gate.

Se ejecuta manualmente o en CI para registrar qué campos expone realmente el
endpoint de alertas recientes. No modifica data/alertas.json.
"""
import json
from collections import Counter

import requests

API = "https://ec.europa.eu/safety-gate-alerts/public/api/notification/mostRecent/?"
HEADERS = {
    "User-Agent": "ProductAlertSpain/4.0 (+https://github.com/progeekts/Product-Alert)",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.5",
}


def shape(value, depth=0):
    if depth >= 3:
        return type(value).__name__
    if isinstance(value, dict):
        return {k: shape(v, depth + 1) for k, v in value.items()}
    if isinstance(value, list):
        return [shape(value[0], depth + 1)] if value else []
    return type(value).__name__


def main():
    response = requests.post(API, headers=HEADERS, json={"language": "es", "page": "0"}, timeout=45)
    response.raise_for_status()
    rows = response.json().get("content") or []
    if not rows:
        raise RuntimeError("Safety Gate no devolvió filas")

    keys = Counter(k for row in rows for k in row)
    print(f"Filas analizadas: {len(rows)}")
    print("Campos raíz (presencia):")
    for key, count in keys.most_common():
        print(f"- {key}: {count}/{len(rows)}")

    sample = rows[0]
    print("\nEstructura de la primera alerta:")
    print(json.dumps(shape(sample), ensure_ascii=False, indent=2, sort_keys=True))

    interesting = ("country", "react", "origin", "categor", "measure", "product", "risk", "trace", "brand", "model", "barcode", "batch")
    print("\nCampos potencialmente relevantes:")
    for key in sorted(sample):
        if any(term in key.lower() for term in interesting):
            value = sample.get(key)
            preview = json.dumps(value, ensure_ascii=False, default=str)
            print(f"- {key}: {preview[:1500]}")


if __name__ == "__main__":
    main()
