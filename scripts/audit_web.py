from pathlib import Path
import sys

errors = []
required = {
    "index.html": ["Product Alert España", "alerta.html?id=", "spain_related", "Fuente oficial"],
    "alerta.html": [
        "data/alertas.json",
        "Abrir publicación oficial",
        "Qué problema presenta",
        "Qué hacer",
        "Medidas oficiales",
        "Relación geográfica",
        "notified_by_spain",
        "spain_follow_up",
    ],
}

for name, needles in required.items():
    p = Path(name)
    if not p.exists():
        errors.append(f"Falta {name}")
        continue
    text = p.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            errors.append(f"{name}: falta marcador requerido: {needle}")
    if "España confirmada" in text:
        errors.append(f"{name}: conserva la etiqueta ambigua «España confirmada»")

# Comprobamos explícitamente las rutas internas estáticas relevantes. Los href
# generados con plantillas JavaScript no deben interpretarse como rutas literales.
for target in ("index.html", "alerta.html", "data/alertas.json"):
    if not Path(target).exists():
        errors.append(f"Recurso interno inexistente: {target}")

if errors:
    print("AUDITORÍA WEB: ERROR")
    for e in errors:
        print("-", e)
    sys.exit(1)

print("AUDITORÍA WEB: OK")
print("Comprobadas estructura, ficha individual, semántica geográfica y recursos internos.")
