# Selector de Monto y Corrección de Activos (BTC)

**Fecha**: 2026-03-10
**Módulos Afectados**: `bot.py`, `gui.py`

## 1. Selector de Monto de Inversión
Se ha implementado la posibilidad de que el usuario defina el monto de dinero a invertir en cada operación directamente desde la interfaz.

**Cambios en `gui.py`:**
- Se añadió un componente `ttk.Spinbox` etiquetado como "Monto Operación ($)".
- El valor inicial se toma de la constante `MONTO_OPERACION` definida en el bot.
- Se vinculó mediante un evento (`<KeyRelease>` y `command`) para que, cada vez que el usuario cambie el número, este se actualice en tiempo real en la instancia activa del bot.

**Cambios en `bot.py`:**
- Se añadió el atributo `self.monto_operacion` a la clase `TradingBot`.
- Se actualizó la lógica de ejecución de órdenes para que utilice este atributo dinámico en lugar de la constante estática.

---

## 2. Corrección de Activos Faltantes (BTC)
Se identificó que el par `BTCUSD` no aparecía en el listado porque el servidor de IQ Option lo reporta como deshabilitado para binarias estándar, pero está disponible bajo el nombre técnico `BTCUSD-OTC-op`.

**Problema:**
El código anterior tenía un filtro de seguridad que ignoraba cualquier activo que terminara en `-op` para evitar duplicados o instrumentos experimentales. Esto causaba que Bitcoin (y otros activos OTC específicos) no se listaran en el desplegable.

**Solución Implementada en `bot.py`:**
Se eliminó la restricción `if "-op" not in name`, permitiendo que el bot mapee y muestre todos los activos habilitados por el broker, incluyendo las versiones OTC de criptomonedas y otros pares que utilizan el sufijo `-op`. Ahora `BTCUSD-OTC-op` aparece correctamente en el dropdown ensanchado.
