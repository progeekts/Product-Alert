# Product Alert España

Central independiente para consultar alertas y retiradas publicadas por organismos oficiales con relevancia para consumidores en España.

## Alcance actual

- AESAN: alertas alimentarias.
- AEMPS: medicamentos y productos sanitarios.
- Estructura preparada para incorporar Red de Alertas de Consumo / productos no alimentarios y otras fuentes oficiales cuando exista un método de extracción estable y verificable.

## Cómo funciona

1. GitHub Actions ejecuta `scripts/scraper.py` dos veces al día.
2. El recolector consulta únicamente fuentes oficiales configuradas en `SOURCES`.
3. Las alertas se normalizan en `data/alertas.json`, conservando siempre el enlace original.
4. `index.html` carga el JSON y permite buscar y filtrar por categoría, organismo y prioridad.

## Principios del proyecto

- No inventar alertas ni completar datos ausentes mediante suposiciones.
- Mantener enlace a la publicación oficial de cada registro.
- Mostrar la fecha de la última comprobación.
- Conservar histórico para facilitar búsquedas posteriores.
- Diferenciar el agregador de los organismos oficiales.

## Desarrollo

```bash
pip install -r scripts/requirements.txt
python scripts/scraper.py
python -m http.server 8000
```

Después abre `http://localhost:8000`.

## Aviso

Esta web es un agregador independiente de información pública. Ante cualquier alerta, deben seguirse las indicaciones de la autoridad competente y de la publicación oficial enlazada.
