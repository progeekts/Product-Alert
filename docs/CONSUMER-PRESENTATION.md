# Contrato de presentación al consumidor

Product Alert debe permitir responder rápidamente a cinco preguntas sin atribuir a la fuente oficial información que no haya publicado.

## 1. ¿Qué producto es?

Mostrar, cuando existan: nombre, marca, modelo, lote, referencia y código/EAN. No completar campos ausentes mediante inferencia.

## 2. ¿Qué problema presenta?

Separar el **riesgo** (por ejemplo, incendio, asfixia o riesgo químico) de la descripción del defecto o incumplimiento. Si la fuente no ofrece detalle suficiente, enlazar la publicación original.

## 3. ¿Qué se ha hecho?

`measures` representa medidas oficiales, del operador económico o de la autoridad. Una retirada, prohibición de venta o corrección no equivale necesariamente a una instrucción directa al consumidor.

## 4. ¿Qué debe hacer el consumidor?

Solo mostrar una instrucción concreta cuando la fuente oficial contenga una recomendación dirigida expresamente a pacientes, usuarios o consumidores. En los demás casos se mostrará una llamada neutra para consultar la publicación oficial.

No reutilizar automáticamente `measures` como `consumer_action`.

## 5. ¿Afecta a España?

Para fuentes españolas, el ámbito se presenta como España. Para Safety Gate se distingue:

- **España confirmada**: los datos oficiales identifican a España como país notificante o país que reacciona a la alerta.
- **UE/EEE**: alerta europea sin evidencia suficiente en el registro ingerido para afirmar comercialización o afectación en España.

Nunca convertir una alerta Safety Gate en «afecta a España» únicamente porque sea visible en el portal europeo.

## Procedencia y transformaciones

Los campos copiados de organismos oficiales son datos de fuente. Las traducciones, agrupaciones de categorías, niveles de prioridad o resúmenes generados por Product Alert deben identificarse como normalizaciones o contenido derivado cuando puedan confundirse con un dato oficial.

## Objetivo de interfaz

Cada tarjeta debe priorizar, en este orden: producto, alcance geográfico, riesgo/problema, identificadores (marca/modelo/lote), medidas oficiales y enlace a la fuente. La publicación original prevalece siempre.
