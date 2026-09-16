# Metodología de datos de Product Alert España

## Principio general

Product Alert agrega publicaciones de fuentes oficiales para facilitar su consulta. La publicación original de la autoridad competente prevalece siempre sobre cualquier normalización o presentación realizada por este proyecto.

## Procedencia

Cada registro conserva `source_id`, organismo, referencia y enlace a la publicación oficial cuando están disponibles. Los datos obtenidos directamente de una fuente oficial se consideran datos de origen; los campos normalizados por Product Alert se distinguen cuando sea necesario.

## Categorías Safety Gate

Safety Gate utiliza categorías oficiales de producto. Product Alert las normaliza a un conjunto reducido de categorías en español para facilitar búsquedas y filtros.

- Si la categoría recibida de Safety Gate se reconoce, `category_basis` vale `official` y `official_category` conserva el valor recibido.
- Si la categoría no puede mapearse de forma fiable, Product Alert puede asignar una categoría de navegación a partir del nombre/descripción del producto. En ese caso `category_basis` vale `derived`.
- La clasificación derivada nunca sustituye ni oculta el enlace a la alerta oficial.

Las categorías visibles incluyen, entre otras: Juguetes, Vehículos, Electrónica y aparatos eléctricos, Infantil, Cosméticos, Ropa y textiles, Productos químicos, Maquinaria y herramientas, Mobiliario, Deporte y ocio, Joyería, Iluminación y Equipos de protección.

## Riesgos y medidas

Los riesgos y medidas se muestran a partir de los datos oficiales disponibles. Product Alert no inventa instrucciones para consumidores. Cuando no existe una recomendación explícita, la web remite a la publicación oficial.

## Ámbito geográfico

Una alerta de Safety Gate se identifica como UE/EEE. No se afirma que el producto se haya comercializado en España únicamente por aparecer en Safety Gate. `spain_confirmed` se utiliza cuando España consta como país notificante o entre los países que han comunicado una reacción/medida asociada a la alerta.

## Disponibilidad y fallos

Las fuentes se comprueban automáticamente. Si una fuente falla o devuelve un resultado sospechosamente vacío, se conserva el último conjunto válido conocido y la fuente se marca como desactualizada (`stale`) en lugar de borrar silenciosamente el histórico.

## Traducciones

Safety Gate publica inicialmente sus alertas en inglés y ofrece traducciones automáticas. Cuando existan diferencias entre versiones lingüísticas, debe consultarse la publicación oficial y tenerse en cuenta la versión original indicada por Safety Gate.
