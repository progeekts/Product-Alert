# Campos públicos de Safety Gate

Product Alert distingue entre datos oficiales publicados por Safety Gate y datos derivados por nuestra normalización.

## Fuentes verificadas

El endpoint público `mostRecent` se usa como índice de alertas recientes. En las ejecuciones observadas expone ID, referencia, fechas, datos básicos de producto, marca/fotografía y tipos de riesgo, pero no el conjunto completo de campos de detalle.

La ficha PDF individual oficial de Safety Gate se usa como fuente de enriquecimiento. En pruebas reales de septiembre de 2026 se comprobó que el PDF contiene texto extraíble sin OCR y puede publicar, según la alerta: país notificante, categoría oficial, producto, nombre, marca, modelo, lote, código de barras, descripción, tipo y descripción del riesgo, normativa, país de origen y medidas adoptadas.

Safety Gate advierte que la versión española del PDF es una traducción automática; si existe discrepancia, prevalece la versión inglesa. Product Alert conserva esta limitación en la procedencia del dato.

## Regla de tratamiento

1. El dato oficial leído de la ficha tiene prioridad sobre una clasificación derivada.
2. Solo se extraen campos delimitados por etiquetas conocidas; si la estructura no es reconocible, se conserva el registro anterior.
3. La extracción de PDF no utiliza OCR.
4. El enriquecimiento es progresivo y limitado por ejecución para evitar descargas masivas innecesarias.
5. Una relación administrativa con España no demuestra por sí sola que el producto se comercializara en España.
6. Las medidas adoptadas por autoridades u operadores se almacenan como medidas oficiales y no se convierten automáticamente en instrucciones al consumidor.
7. Cada alerta mantiene enlace a la publicación oficial y, cuando se enriquece, referencia a la ficha PDF utilizada.

## Resiliencia

Un fallo del índice, de una ficha PDF o de la extracción no elimina alertas válidas ya almacenadas. La actualización conserva el último dato conocido y el control de calidad se ejecuta antes de publicar el JSON generado.

## Evolución

La clasificación textual permanece únicamente como respaldo. A medida que una alerta obtiene categoría oficial desde su ficha, `category_basis` pasa a `official` y `category_method` a `safety_gate_pdf`.
