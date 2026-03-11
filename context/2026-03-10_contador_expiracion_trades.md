# Implementación de Contador de Expiración en Tiempo Real

Se ha añadido un contador regresivo para las órdenes activas, similar al que se muestra en la plataforma web de IQ Option, para mejorar la visibilidad del tiempo restante de cada operación.

## Cambios Realizados

### 1. Cálculo de Expiración (`bot.py`)
- Al abrir una orden (Binaria o Digital), el bot calcula el timestamp de expiración basándose en la configuración `EXPIRACION` (actualmente 1 min).
- Este timestamp se envía a la GUI a través del evento `order` bajo la clave `exp_at`.

### 2. Ticker de UI (`gui.py`)
- Se implementó un rastreador de expiración (`exp_tracker`) que guarda los IDs de las órdenes abiertas.
- Un nuevo proceso periódico `update_order_timers` se ejecuta cada segundo en el hilo principal de la UI.
- Este proceso calcula el tiempo restante y actualiza dinámicamente la columna "Resultado" con el formato **Expira: MM:SS**.
- Cuando el tiempo se agota, muestra **Cerrando...** hasta que el bot confirma el resultado final (Win/Loss).

### 3. Fluidez del Análisis
- Gracias a la arquitectura multi-hilo implementada anteriormente, este contador no interfiere con el análisis de indicadores ni con el movimiento del gráfico de velas.

## Verificación
- El contador comienza inmediatamente al abrir una orden.
- El tiempo desciende de forma precisa segundo a segundo.
- Al llegar a 0, la celda cambia momentáneamente antes de recibir el "WIN" o "LOSS" final del servidor.
