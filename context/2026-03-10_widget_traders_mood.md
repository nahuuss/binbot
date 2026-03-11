# Implementación Widget: Sentimiento de Operadores (Traders Mood)

**Fecha**: 2026-03-10
**Módulos Afectados**: `bot.py`, `gui.py`

## 1. Extracción de Datos (`bot.py`)
El usuario solicitó replicar el widget flotante gráfico de "Sentimiento de Operadores" de IQ Option, que denota qué porcentaje de operaciones en vivo son compras (CALL / Sube) en tiempo real respecto a un activo.
Investigando la API no oficial, se descubrió la existencia del canal WebSocket interno `api.start_mood_stream(activo, "turbo-option")` y su respectivo acceso pasivo `api.get_traders_mood(activo)`.

**Solución Implementada:**
1. Al arrancar el bot, y cada vez que el usuario selecciona un nuevo activo comercial en el Combobox desde la UI (`def set_asset(self, new_asset)`), el bot interrumpe el Stream de sentimiento viejo y se adhiere pasivamente al canal de telemetría del nuevo activo.
2. Dentro del gran ciclo infinito de ejecución principal (`run_trading_loop`), justo donde se piden las velas historicas y se procesan los osciladores, ahora el sistema intenta recuperar asíncronamente este radio de operaciones invocando `self.api.get_traders_mood(self.current_asset)`.
3. El valor capturado en coma flotante (de 0.0 a 1.0) se transmite empaquetado como el atributo `'mood_call'` directo al Frontend de Tkinter a través del canal inter-hilos (Payload de Métricas).

---

## 2. Renderizado del Gráfico en Interfaz Visual (`gui.py`)
Para no sobrecargar la librería y el procesador renderizando barras en Matplotlib, se diseñó un widget personalizado utilizando herramientas nativas del núcleo C de Tkinter (`tk.Canvas`).

**Arquitectura del Widget:**
Se integró paralelamente a la izquierda del gráfico histórico de Matplotlib un `<Frame>` vertical fijo sin propagación, que alberga:
- Un `<Label>` verde superior informando el % neto (Multiplicado por 100 y truncado a entero) de posiciones alcistas vigentes (`SUBE`).
- Un primitivo `<Canvas>` central estirado de tamaño flexible de donde se purga la pantalla por fotograma y se pintan con la herramienta `create_rectangle` dos rectángulos entrelazados cuya altura Y límite es un reflejo exacto y matemático de la cota flotante enviada desde el Background Thread (Verde arriba si Call, Rojo abajo si Put iterando `h * mood_call`).
- Un `<Label>` rojo base computando el inverso nominal de la estadística alcista (1.0 - x) que informa los bajistas (`BAJA`).
