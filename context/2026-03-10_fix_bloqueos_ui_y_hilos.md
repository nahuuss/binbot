# Solución de Bloqueos de UI y Refresco de Trades

Se han corregido los problemas de congelamiento de la interfaz y la falta de actualización del contador/trades durante las operaciones.

## Cambios Realizados

### 1. Seguimiento de Órdenes No Bloqueante (`bot.py`)
- Se eliminó el uso de `api.check_win_v3` y `api.check_win_digital_v2` dentro del bucle principal de análisis.
- Las órdenes ahora se monitorean en un hilo independiente (`_wait_for_result`).
- Esto permite que el bot siga enviando métricas (RSI, precio, contador) a la GUI mientras hay una operación abierta.

### 2. Cooldown Basado en Tiempo (`bot.py`)
- Se reemplazó el `time.sleep(60)` que congelaba el bot tras cada operación por un chequeo de timestamp (`last_trade_time`). 
- El bot sigue analizando y mostrando datos durante el minuto de espera, pero no abre nuevas órdenes hasta que pase el tiempo.

### 3. Cambio de Activos Asíncrono (`gui.py`)
- El método `on_asset_change` ahora lanza el cambio de activo en un hilo `daemon`.
- Esto evita que la interfaz de Tkinter entre en estado "No Responde" mientras se desconectan y conectan los streams de datos del activo en IQ Option.

### 4. Estabilidad y Errores
- Se mejoró el manejo de fallback a Digitales si las Binarias están suspendidas.
- Se corrigieron errores de indentación y sintaxis introducidos durante la refactorización.

## Verificación
- El contador de "Próximo análisis" ahora es fluido y no se detiene al abrir un trade.
- El historial de órdenes se actualiza a "WIN/LOSS" automáticamente al finalizar el tiempo de expiración.
- La interfaz permanece respondante en todo momento.
