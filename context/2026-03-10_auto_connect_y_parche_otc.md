# Parche de Activos OTC y Auto-Arranque del Bot

**Fecha**: 2026-03-10
**Módulos Afectados**: `bot.py`, `gui.py`

## 1. Mapeo Dinámico de Activos Faltantes (AIG-OTC y otros)
La librería no-oficial `iqoptionapi` posee un archivo de constantes llamado `constants.py` que almacena de forma rígida (hardcoded) un diccionario (`OP_code.ACTIVES`) que asocia nombres de string (como `"EURUSD"`) con los ID enteros internos del servidor (como `1`).

**Problema:**
La API de IQ Option ha añadido decenas de instrumentos nuevos OTC (por ejemplo, `AIG-OTC`, `ALIBABA-OTC`, diversas criptos OTC) que **NO** existen en el diccionario de la librería. Como consecuencia, al intentar hacer un `api.get_candles()` de esos activos, la librería arrojaba `Asset ... not found on consts` y devolvía vacío (`None`).

**Solución Implementada en `bot.py`:**
Se agregó un bloque de escaneo dinámico en la rutina de arranque del bot (justo después del `connect()`). El bot ahora pide al servidor el gran paquete de inicialización cruda (`self.api.get_all_init_v2()`). Este paquete contiene un sub-diccionario `binary` y `turbo` que aloja **todos** los IDs existentes y sus nombres.
El bot itera este paquete gigante, extrae los ID numéricos de los OTC desconocidos y los inyecta dinámicamente en memoria dentro de `OP_code.ACTIVES` (p. ej. `OP_code.ACTIVES["AIG-OTC"] = 2109`). Ahora la librería cree que siempre supo la respuesta y es capaz de recuperar velas y operar sin errores de constante faltante.

---

## 2. Auto-Arranque al Abrir la Interfaz Gráfica (GUI)
El usuario solicitó que "al iniciar la app debe conectar de forma automatica".

**Problema:**
Anteriormente, abrir `gui.py` solo cargaba la ventana en estado "Detenido" y el usuario debía clickear en "INICIAR BOT" manualmente para disparar toda la lógica.

**Solución Implementada en `gui.py`:**
Se sumó la línea `self.root.after(500, self.start_bot)` al final del constructor gráfico (`setup_ui`). Ahora, 0.5 segundos después de que la ventana se dibuja correctamente en pantalla, dispara automáticamente las funciones de conexión al bróker, logueo en background y análisis de mercado sin intervención humana.

---

## 3. Bypass de Exception Thread Crash (`KeyError: 'underlying'`)
**Problema:**
Al consultar la lista de activos disponibles, se estaba llamando a la función interna de la librería `api.get_all_open_time()`. Esta función está programada para disparar 3 hilos (threads) independientes en paralelo para buscar opciones Binarias, Digitales y Forex.
Sin embargo, un fallo interno de la librería provocaba que el hilo de opciones Digitales se colgara (arrojando un feo error `KeyError: 'underlying'` en la consola, aunque no detuviera el programa).

**Solución Implementada en `bot.py`:**
Se eliminó por completo el uso de la función defectuosa `get_all_open_time()`. 
Puesto que en el paso previo (Punto 1) ya obtenemos el gran paquete `init_v2_data` directamente desde el WebSocket para parchear las constantes, se aprovechó este mismo diccionario para extraer directamente el listado de activos.
Se evaluaron matemáticamente los booleanos `active_data.get("enabled")` y `not active_data.get("is_suspended")` directamente en memoria pura, prescindiendo del llamado problemático de la librería. Esto silencia el error rojo por consola respetando y unificando el armado rápido del Combobox sin recurrir a multithreading de terceros rotos.
