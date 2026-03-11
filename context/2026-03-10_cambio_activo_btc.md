# Bot Actualizado para Trades con Bitcoin (BTCUSD) de forma contínua
Se ajustó el comportamiento principal del bot en `bot.py` según el requerimiento del usuario:
1. **Activo**: Se cambió el activo de `EURUSD` a `BTCUSD` usando el ticker oficial del Broker.
2. **Ejecución Contínua y Robusta**: Se reforzó el bloque `try...except` del ciclo infinito. Ahora el bot valida mediante `api.check_connect()` si la API de Python perdió la conexión con WebSockets del servidor de IQ Option. En caso de corte de red, el bot reconectará en automático en lugar de detenerse.
