# Implementación del Bot de Trading (bot.py)

Se ha creado el archivo principal `bot.py` que contiene toda la lógica automatizada:

1. **Gestión de Conexión**: Conecta usando variables de entorno `.env` igual que el script de prueba. Cambia el saldo a cuenta de Práctica y mantiene el status.
2. **Obtención de datos**: En un bucle (`while True`), cada 10 segundos extrae las velas de un mercado específico (por defecto `EURUSD`, velas de 1 minuto).
3. **Indicador RSI**: Se implementó una función matemática `calcular_rsi` en código puro (sin depender de `pandas` o librerías pesadas externas) para trazar el indicador de fuerza relativa RSI usando el método "Wilder's Smoothing".
4. **Estrategia**:
   - Si RSI > 70 (Sobrecompra) -> Se activa una orden a la baja (`put`). 
   - Si RSI < 30 (Sobreventa) -> Se activa una orden al alza (`call`).
5. **Ejecución y Control**: Utiliza `api.buy()` para entrar al mercado, verifica el resultado al terminar el tiempo de la vela ganada/perdida/empatada con `check_win_v3`, notifica beneficio y entra en pausa de 60 segundos después de cada operación.

Este bot puede encenderse desde consola y se quedará escaneando y operando automáticamente.
