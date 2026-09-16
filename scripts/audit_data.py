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
            if a.get("spain_confirmed") is not True and "España" in str(a.get("consumer_action", "")) and "no implica" not in str(a.get("consumer_action", "")):
                errors.append(f"{ref}: posible afirmación geográfica no respaldada")
            if a.get("category") == "Otros productos":
                warnings.append(f"{ref}: categoría pendiente de mejorar")
        # Las medidas de fabricante/autoridad no deben presentarse automáticamente
        # como una instrucción específica para el consumidor.
        action = str(a.get("consumer_action") or "")
        measures = a.get("measures") or []
        if measures and action and action not in {
            "Consulta la publicación oficial para conocer las medidas aplicables.",
            "Consulta las medidas oficiales de la alerta. La presencia en Safety Gate no implica por sí sola que el producto se haya comercializado en España.",
        }:
            warnings.append(f"{ref}: revisar separación entre medidas y consejo al consumidor")

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
