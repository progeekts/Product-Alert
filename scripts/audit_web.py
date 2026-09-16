from pathlib import Path
import re, sys

errors=[]
required={
    'index.html':['Product Alert España','alerta.html?id=','spain_related','Fuente oficial'],
    'alerta.html':['data/alertas.json','Fuente oficial','Medidas oficiales','Qué hacer','Relación con España'],
}
for name,needles in required.items():
    p=Path(name)
    if not p.exists():
        errors.append(f'Falta {name}')
        continue
    text=p.read_text(encoding='utf-8')
    for needle in needles:
        if needle not in text:
            errors.append(f'{name}: falta marcador requerido: {needle}')
    if 'España confirmada' in text:
        errors.append(f'{name}: conserva la etiqueta ambigua «España confirmada»')

# Enlaces internos que deben apuntar a archivos versionados.
index=Path('index.html').read_text(encoding='utf-8') if Path('index.html').exists() else ''
for href in re.findall(r'href=["\']([^"\']+)', index):
    if href.startswith(('http://','https://','#','mailto:','javascript:')):
        continue
    target=href.split('?',1)[0]
    if target and not Path(target).exists():
        errors.append(f'index.html: enlace interno inexistente: {target}')

if errors:
    print('AUDITORÍA WEB: ERROR')
    for e in errors: print('-',e)
    sys.exit(1)
print('AUDITORÍA WEB: OK')
print('Comprobadas estructura, ficha individual, semántica geográfica y rutas internas.')
