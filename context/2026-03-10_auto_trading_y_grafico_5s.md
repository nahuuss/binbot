# Auto-Trading y Gráfico en Tiempo Real (5s)

## Cambios Implementados

### 1. Checkbox de Auto-Trading (`gui.py`)
- Nuevo checkbox "AUTO-TRADING (Operar Automáticamente)" en el panel de controles
- Activa/desactiva el flag `bot.auto_trading`
- Cuando está desactivado, solo funcionan los botones FORZAR CALL/PUT

### 2. Sistema de Scoring con Sentimiento (`bot.py`)
Al activar auto-trading, el bot usa un sistema de puntos (4 indicadores):

| Indicador | Señal PUT (+1) | Señal CALL (+1) |
|---|---|---|
| RSI | ≥ 70 (sobrecompra) | ≤ 30 (sobreventa) |
| Bollinger | Precio ≥ BB Superior | Precio ≤ BB Inferior |
| Tendencia | EMA < SMA (bajista) | EMA > SMA (alcista) |
| Mood | < 35% apuestan sube | > 65% apuestan sube |

**Se requieren 3 de 4 puntos** para ejecutar una operación automática.

### 3. Gráfico con Velas de 5 Segundos (`bot.py` + `gui.py`)
- Se obtienen 60 velas de 5 segundos (~5 minutos de historia)
- El eje X muestra timestamps HH:MM:SS
- Los indicadores técnicos siguen usando velas de 60s para mayor estabilidad

### 4. Intervalo de Análisis
- Reducido de 10s a 6s para análisis más frecuente
