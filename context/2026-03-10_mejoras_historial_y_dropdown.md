# Mejoras en Historial y UI del Dropdown

**Fecha**: 2026-03-10
**Módulos Afectados**: `bot.py`, `gui.py`

## 1. Recuperación de Historial de Operaciones (`bot.py`)
El usuario solicitó que el bot traiga el historial de operaciones ("traer historico").

**Solución Implementada:**
- Se añadió una rutina en `bot.py` que, tras conectar y parchear los IDs de los activos, realiza consultas a la API de IQ Option mediante `get_position_history_v2`.
- El bot recupera las últimas 10 operaciones de tipo `"binary-option"` y 10 de tipo `"turbo-option"`.
- Estas operaciones se formatean (ID, Hora, Dirección, Inversión, Resultado, Beneficio) y se emiten a la interfaz mediante el comando `'order'`.
- En `gui.py`, se modificó el manejador de eventos para que verifique si el ID de la orden ya existe en la tabla (`tree.exists(oid)`) antes de insertarla, evitando duplicidad visual entre el historial cargado y las nuevas órdenes en vivo.

## 2. Expansión del Dropdown de Activos (`gui.py`)
El usuario notó que el dropdown (Combobox) de activos era pequeño y no permitía ver bien los nombres o desplazarse cómodamente.

**Solución Implementada:**
- Se aumentó el atributo `width` del Combobox de `12` a `20` para acomodar nombres de activos largos (como `BTCUSD-OTC`).
- Se definió el atributo `height` en `15` para que el menú desplegable muestre más elementos simultáneamente sin requerir tanto desplazamiento.
- Se ajustó el empaquetado del widget (`pack`) para que se expanda horizontalmente (`fill=tk.X`) ocupando el espacio disponible en su panel.
