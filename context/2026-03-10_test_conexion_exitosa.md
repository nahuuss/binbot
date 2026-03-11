# Prueba de Conexión Exitosa

Se ejecutó el script `test_connection.py` con las credenciales configuradas por el usuario.
El resultado fue exitoso:
- La API logró autenticarse en IQ Option.
- Se cambió correctamente al balance de práctica (`PRACTICE`).
- Se imprimió el balance de la cuenta de práctica (ej. `$10673.57`).
- Se obtuvieron datos del mercado en vivo (las últimas 5 velas de 1 minuto del par `EURUSD`).

Con esto comprobamos que la librería `iqoptionapi` funciona correctamente desde Github y que el entorno de desarrollo local está listo para programar el bot.
