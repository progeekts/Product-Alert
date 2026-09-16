# Product Alert España

Observatorio independiente y gratuito para consultar en un único lugar alertas y retiradas publicadas por fuentes oficiales relevantes para consumidores en España.

## Estado del proyecto

La web está planteada como un servicio de consulta estable, no como un listado manual. El sistema recopila, normaliza, conserva y presenta alertas con trazabilidad hacia la publicación oficial. Los datos oficiales prevalecen siempre sobre los resúmenes y clasificaciones del proyecto.

## Cobertura

Actualmente se integran:

- **AESAN**: alertas alimentarias.
- **AEMPS**: medicamentos, productos sanitarios y cosméticos.
- **Safety Gate de la Comisión Europea**: productos no alimentarios, con enriquecimiento progresivo desde las fichas PDF oficiales cuando están disponibles.

Safety Gate cubre la UE/EEE. Que España figure como país notificante o de seguimiento no demuestra por sí solo que un producto se comercializara en España; la interfaz conserva esa distinción.

## Cómo funciona

1. GitHub Actions ejecuta la actualización automática dos veces al día.
2. Los recolectores consultan fuentes oficiales configuradas y procesan cada fuente de forma aislada.
3. Si una fuente falla, se evita borrar silenciosamente el último conjunto válido conocido.
4. Los registros se normalizan y deduplican en `data/alertas.json`, manteniendo el enlace a la publicación oficial.
5. Safety Gate se enriquece progresivamente desde sus fichas PDF oficiales mediante extracción de texto, sin OCR.
6. Antes de publicar se ejecutan controles automáticos de integridad de datos y de la interfaz web.
7. `index.html` ofrece búsqueda y filtros; `alerta.html` presenta la ficha orientada al consumidor.

## Principios de datos

- No inventar alertas ni completar campos ausentes mediante suposiciones.
- Mantener trazabilidad hacia la fuente oficial.
- Separar información oficial de normalizaciones y clasificaciones derivadas.
- No convertir medidas adoptadas por autoridades u operadores en instrucciones para el consumidor.
- No inferir comercialización en España a partir de una mera relación administrativa con una alerta europea.
- Conservar histórico y último dato válido cuando una fuente sufre un fallo temporal.
- Mostrar cuándo se realizó la última comprobación y el estado de las fuentes.

La metodología detallada se encuentra en `docs/DATA-METHODOLOGY.md`, `docs/CONSUMER-PRESENTATION.md` y `docs/SAFETY-GATE-FIELDS.md`.

## Operación y mantenimiento

El proyecto entra en modo de operación estable una vez cerrada la versión de producción. Las mejoras futuras deberían responder a una de estas causas: cambio real en una fuente oficial, error detectado, nueva fuente oficial con utilidad clara o mejora sustancial de accesibilidad/experiencia.

Ante un cambio en una fuente:

1. comprobar el workflow y sus logs;
2. verificar que el histórico válido sigue conservado;
3. adaptar el extractor sin rebajar las garantías semánticas;
4. ejecutar las auditorías de datos y web;
5. revisar una muestra real antes de fusionar.

No es recomendable añadir fuentes no oficiales únicamente para aumentar el número de registros.

## Desarrollo local

```bash
pip install -r scripts/requirements.txt
python scripts/scraper.py
python -m http.server 8000
```

Después abre `http://localhost:8000`.

## Estructura principal

- `index.html`: buscador y listado de alertas.
- `alerta.html`: ficha individual.
- `data/alertas.json`: registro normalizado generado.
- `scripts/`: extracción, enriquecimiento, auditorías e informes.
- `.github/workflows/`: actualización y controles automáticos.
- `docs/`: metodología y decisiones de presentación de datos.

## Aviso

Product Alert España es un proyecto independiente y no pertenece a ninguna Administración. Facilita la consulta de información pública y no sustituye las instrucciones de los organismos competentes, fabricantes ni profesionales sanitarios. Ante cualquier discrepancia, prevalece la publicación oficial enlazada en cada alerta.
