# Análisis de Operatoria de Opciones Binarias y Prevención de Errores

El día de hoy se analizó el funcionamiento del bot en base a cómo operan las Opciones Binarias reales en la plataforma de IQ Option.

## ¿Cómo opera el bot las Binarias?
Tal cual como se observa en la plataforma web (donde uno apuesta si el precio subirá o bajará en una franja de tiempo determinada), el bot réplica esta misma acción a través de la función `api.buy()`.

1. **Análisis de Entrada**: El bot no ingresa aleatoriamente. Utiliza la estrategia de *Consenso* (RSI + Bandas Bollinger + Medias Móviles) para predecir si en el próximo minuto la vela cerrará arriba o abajo del precio de entrada.
2. **Apuesta (Trade Corto)**: Al detectar el consenso, el bot lanza la instrucción `api.buy(monto, activo, direccion, tiempo)`. 
   - Si la dirección es `call` (Sube / Botón Verde), apuesta a que cerrará arriba.
   - Si la dirección es `put` (Baja / Botón Rojo), apuesta a que cerrará abajo.
3. **Expiración y Resultado**: El bot utiliza la función interna de la API `api.check_win_v3` la cual entra en un compás de espera automático equivalente al tiempo de expiración (ej. 1 minuto). Una vez que la plataforma cierra la opción, la función retorna el **Beneficio** obtenido. Si es mayor a 0, se ganó la apuesta (WIN). Si es menor, se perdió la inversión (LOSS).

## Testeo y Prevención de Errores
Se añadió un bloque robusto de captura de errores (`try/except`) envolviendo la ejecución de la orden. Esto se hizo para testear y contemplar todos los errores que la API podría lanzar al intentar apostar en una ventana de tiempo específica.

**Los posibles errores que ahora el bot captura y reporta amigablemente en el Dashboard son:**
- **Rechazo por Mercado Cerrado**: La API devuelve `False` si el exchange de ese activo cerró en ese instante de tiempo.
- **Rechazo por Saldo**: Si el balance de práctica o real no es suficiente para cubrir el `MONTO_OPERACION`.
- **Rechazo por Payout Bajo / Bloqueo de Riesgo**: IQ Option a menudo bloquea las compras en opciones binarias temporales si su retorno de inversión (ROI) cae al 0% por volatilidad. 
- **Errores Críticos de Red**: Si la red se cae *justo* al enviar la orden o durante la espera del `check_win_v3`, el bot capturará la excepción para no congelar ni crashear la interfaz gráfica, indicándole al usuario el problema y continuando su ciclo.

## Mercados OTC en IQ Option
**OTC** significa *"Over The Counter"* (en el mostrador). En el mundo financiero tradicional significa que una acción o activo se comercia directamente entre dos partes fuera de una bolsa de valores centralizada. 

En **IQ Option**, el prefijo OTC (ej: `BTCUSD-OTC` o `EURUSD-OTC`) hace referencia a un mercado creado internamente por el propio broker para permitir operar **los fines de semana y feriados**, días en los que los mercados bursátiles mundiales reales están cerrados y no emiten precios oficiales.

**Características de OTC:**
- Los precios OTC son dictados por los algoritmos del propio broker basándose en los volúmenes de oferta y demanda internos de sus usuarios.
- Suelen tener mayor volatilidad y comportamientos erráticos en indicadores técnicos, ya que no siguen el libro de órdenes mundial real.
- Durante los fines de semana (sábado y domingo), las divisas normales (`EURUSD`, `BTCUSD` estándar de binarias) son marcadas como "Suspendidas" o "Cerradas". En la GUI y el bot **se debe cambiar al mercado OTC explícito (`BTCUSD-OTC`) para que el bot pueda colocar la apuesta binaria.**
