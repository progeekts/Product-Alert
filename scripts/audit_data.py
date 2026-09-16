import json
import sys
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data" / "alertas.json"


def main():
    payload = json.loads(DATA.read_text(encoding="utf-8"))
    alerts = payload.get("alerts", [])
    errors = []
    warnings = []

    if not alerts:
        errors.append("El registro de alertas está vacío")

    ids = [a.get("id") for a in alerts if a.get("id")]
    duplicate_ids = [k for k, v in Counter(ids).items() if v > 1]
    if duplicate_ids:
        errors.append(f"IDs duplicados: {len(duplicate_ids)}")

    for a in alerts:
        ref = a.get("reference") or a.get("id") or "sin referencia"
        if not a.get("source_id"):
            errors.append(f"{ref}: falta source_id")
        if not a.get("link"):
            errors.append(f"{ref}: falta enlace oficial")
        if not a.get("title"):
            errors.append(f"{ref}: falta título")

        if a.get("source_id") == "eu_safety_gate":
            if a.get("category_basis") not in {"official", "derived"}:
                errors.append(f"{ref}: category_basis inválido")
            # spain_confirmed queda como campo legado y nunca debe afirmar presencia comercial.
            if a.get("spain_confirmed") is True:
                errors.append(f"{ref}: spain_confirmed no puede usarse como prueba de comercialización")
            for key in ("notified_by_spain", "spain_follow_up", "spain_related"):
                if key in a and not isinstance(a.get(key), bool):
                    errors.append(f"{ref}: {key} debe ser booleano")
            expected_related = bool(a.get("notified_by_spain") or a.get("spain_follow_up"))
            if bool(a.get("spain_related")) != expected_related:
                errors.append(f"{ref}: spain_related incoherente")

            action = str(a.get("consumer_action") or "").lower()
            unsupported = ("comercializado en españa", "vendido en españa", "distribuido en españa")
            if any(term in action for term in unsupported):
                errors.append(f"{ref}: posible afirmación comercial/geográfica no respaldada")
            if a.get("category") == "Otros productos":
                warnings.append(f"{ref}: categoría pendiente de mejorar")

        # Las medidas de fabricante/autoridad no deben presentarse automáticamente
        # como una instrucción específica para el consumidor.
        action = str(a.get("consumer_action") or "")
        measures = a.get("measures") or []
        if measures and action and action in measures:
            warnings.append(f"{ref}: consumer_action coincide con una medida oficial")

    categories = Counter(a.get("category") or "Sin categoría" for a in alerts)
    sources = Counter(a.get("source_id") or "sin_source_id" for a in alerts)

    print(f"Alertas auditadas: {len(alerts)}")
    print("Fuentes:", dict(sources))
    print("Categorías:", dict(categories))
    print(f"Advertencias: {len(warnings)}")
    for item in warnings[:30]:
        print("WARN:", item)
    if len(warnings) > 30:
        print(f"WARN: ... y {len(warnings) - 30} advertencias más")

    if errors:
        print(f"Errores: {len(errors)}")
        for item in errors:
            print("ERROR:", item)
        return 1
    print("Auditoría estructural: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
