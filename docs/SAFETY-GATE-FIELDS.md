# Campos públicos de Safety Gate

Product Alert distingue entre datos oficiales publicados por Safety Gate y datos derivados por nuestra normalización.

La documentación pública de la Comisión Europea indica que pueden publicarse, entre otros, estos campos de producto: categoría, marca, modelo/tipo, código de barras, país de origen, descripción breve y fotografía.

## Regla de tratamiento

1. Si el dato oficial está disponible y el extractor puede leerlo, se conserva como dato oficial.
2. Las categorías oficiales tienen prioridad absoluta sobre cualquier clasificación interna.
3. Si la categoría oficial no está disponible o no puede mapearse, puede aplicarse una clasificación textual de respaldo. Se marca como `category_basis: derived` y nunca se presenta como categoría oficial.
4. Una relación administrativa con España (país notificante o seguimiento) no se interpreta como prueba automática de comercialización en España.
5. Las medidas adoptadas por autoridades u operadores no se convierten automáticamente en instrucciones al consumidor.

## Objetivo de enriquecimiento

La clasificación textual es una solución de respaldo. El objetivo técnico es ampliar progresivamente el extractor para recuperar directamente todos los campos públicos que Safety Gate exponga de forma fiable, manteniendo trazabilidad hacia la publicación oficial.
