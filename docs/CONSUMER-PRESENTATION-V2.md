# Presentación de alertas al consumidor · v2

Product Alert debe responder de forma separada a cinco preguntas: qué producto es, cuál es el problema, qué medidas oficiales constan, qué debe hacer el consumidor y qué relación documentada tiene la alerta con España.

## Alcance geográfico

Las fuentes españolas (AESAN/AEMPS) se muestran como `España`.

Las alertas Safety Gate se muestran como:

- `UE/EEE · Notificada por España` cuando `notified_by_spain=true`.
- `UE/EEE · Seguimiento de España` cuando `spain_follow_up=true` y España no es el país notificante.
- `UE/EEE` cuando no existe ninguna de las señales anteriores.

Ninguna de estas etiquetas debe transformarse automáticamente en afirmaciones como «vendido en España», «comercializado en España» o «afecta a España». Esas afirmaciones requieren evidencia específica en la publicación oficial.

## Medidas y recomendaciones

`measures` describe medidas o actuaciones oficiales/empresariales que constan en la fuente. `consumer_action` debe reservarse para una recomendación explícita dirigida al consumidor o, cuando no se haya podido estructurar una, para una indicación prudente de consultar la publicación oficial.

## Categorías

Cuando `category_basis=official`, la categoría procede de los datos oficiales estructurados. Cuando `category_basis=derived`, se utiliza únicamente como ayuda de navegación y no debe presentarse como clasificación oficial.

## Ficha individual

Cada alerta dispone de una URL interna estable basada en su `id`: `alerta.html?id=<id>`. La ficha mantiene visible el enlace a la publicación oficial y recuerda que la fuente original prevalece sobre el resumen de Product Alert.