# Hoja de ruta · Product Alert España

## Misión
Convertir Product Alert España en un observatorio independiente, gratuito y trazable de alertas y retiradas de productos relevantes para consumidores en España.

## Principios
1. La fuente original prevalece siempre.
2. No publicar registros inventados ni completar campos mediante suposiciones.
3. Una fuente que falla no debe borrar el histórico válido ya recopilado.
4. Diferenciar claramente datos oficiales, normalización automática y resúmenes derivados.
5. Cada registro debe conservar enlace a la publicación oficial.
6. Priorizar utilidad para el consumidor sobre volumen de datos.

## Fase actual · Integridad
- AESAN: alimentación.
- AEMPS: medicamentos, productos sanitarios y cosméticos.
- Estado de salud de fuentes visible en la web.
- Deduplicación y normalización.
- Conservación del último conjunto conocido cuando una fuente falla.

## Próxima cobertura
### Safety Gate
Sistema europeo oficial de alertas rápidas para productos peligrosos no alimentarios. Objetivo: integrar únicamente mediante un mecanismo público, reproducible y validado, conservando identificador de alerta, categoría, producto, marca/modelo, riesgo, medidas adoptadas, país y enlace oficial.

### Red de Alerta española
Investigar una vía oficial estable para incorporar alertas nacionales de productos no alimentarios y evitar depender de scraping frágil.

### Vehículos
Incorporar retiradas/campañas cuando exista una fuente pública oficial apta para consulta automatizada y trazable.

## Evolución de las fichas
Cada alerta debería responder, cuando la fuente facilite esos datos, a:
- Qué producto está afectado.
- Marca, modelo, referencia, lote o código de barras.
- Qué problema se ha detectado.
- Qué riesgo existe.
- Qué medida se ha adoptado.
- Qué debería hacer el consumidor.
- Fecha y organismo responsable.
- Enlace a la publicación oficial.

## Funciones previstas
- URL individual por alerta.
- Histórico por producto/marca/categoría.
- Buscador tolerante a referencias, lotes y modelos.
- Filtros por riesgo, organismo, categoría, fecha y medida adoptada.
- Resumen en lenguaje sencillo claramente identificado como resumen automático.
- Página pública de metodología, cobertura y estado de fuentes.
- Feed RSS/JSON para reutilización de las alertas.
- Preparación para avisos/suscripciones en una fase posterior.

## Criterio de incorporación de fuentes
Una fuente nueva debe ser oficial o institucional, públicamente accesible, trazable, suficientemente estable para automatización y aportar información que pueda enlazarse a su origen. Si no cumple estos requisitos, se mantiene fuera del agregador hasta disponer de un método fiable.
