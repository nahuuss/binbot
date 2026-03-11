# Mejoras Completas del Bot + Estrategias de Anticipación - 2026-03-10/11

## Cambios Implementados

### 1. Martingala Controlada
- Duplica monto tras cada pérdida consecutiva (max 4 pasos: $1 → $2 → $4 → $8 → $16)
- Se resetea automáticamente al ganar
- Se resetea al alcanzar el máximo de pasos

### 2. Stop-Loss / Take-Profit
- **Stop-Loss**: Detiene auto-trading si pierde 10% del balance inicial
- **Take-Profit**: Detiene auto-trading si gana 15% del balance inicial
- Se puede reactivar desde el checkbox

### 3. Filtro de Volatilidad
- No opera cuando las Bandas de Bollinger están muy estrechas (< 0.02% del precio)
- Evita operar en mercados laterales sin tendencia

### 4. Timing de Entrada
- Solo entra en los primeros 30 segundos de la vela
- Maximiza el tiempo de exposición favorable

### 5. Historial Persistente (CSV + TXT)
- `trade_history.csv`: Registro de cada trade con timestamp, asset, dirección, monto, resultado, profit, balance, mood, RSI
- `analysis_log.txt`: Log detallado de CADA análisis con todos los indicadores para encontrar mejoras en la estrategia

### 6. Marcadores de Trades en el Gráfico
- ▲ Verde con monto = WIN
- ▼ Rojo con monto = LOSS
- ○ Amarillo = Pendiente

### 7. Dirección con Sube/Baja
- Tabla muestra "CALL ↑ Sube" / "PUT ↓ Baja" en vez de solo CALL/PUT

### 8. Contador PnL + Win Rate
- Header muestra: W:X | L:X | XX% | P/L: $X.XX
- Verde si ganancia positiva, rojo si negativa

### 9. Nombre Dinámico del Activo
- El título "Análisis en Vivo (XXX)" se actualiza al cambiar de activo

### 10. Sentimiento en Strikes
- Agregadas condiciones de sentimiento para PUT (Mood < 45%) y CALL (Mood > 55%)

## Estrategias de Anticipación (Sistema de Scoring Ponderado)

El sistema ahora usa 5 estrategias de anticipación combinadas con pesos:

| Estrategia | Peso Anterior | Nuevo Peso | Descripción |
|-----------|---------------|-------------|-------------|
| Micro-Momentum | 20% | **25%** | Dirección reciente del precio (últimas 10 velas 5s) |
| Indicadores Técnicos | 15% | **20%** | RSI + BB + EMA/SMA como score combinado |
| Mood Momentum | 25% | **15%** | Tendencia del sentimiento (aceleración/desaceleración) |
| Divergencia Precio/Mood | 15% | **15%** | Detecta reversiones cuando precio y sentimiento divergen |
| Sentimiento Actual | 15% | **10%** | Mood CALL/PUT como score base |
| Rate of Change (ROC) | 5% | **10%** | Velocidad del movimiento del precio |
| Fade the Crowd | 5% | **5%** | Contrarian en sentimiento extremo (>85%) |

- **Umbral**: Score ≥ +0.20 → CALL, Score ≤ -0.20 → PUT
- Score visible en tiempo real en la GUI
- Todos los scores guardados en `analysis_log.txt`

## Mejoras del Gráfico e Interfaz
- Marcadores de trades ahora con fondo y borde (no se superponen)
- Solo se muestran los últimos 5 marcadores
- Anotaciones escalonadas para evitar overlap
- **Gráfico Interactivo**: Añadida barra de herramientas (NavigationToolbar2Tk) para pan (desplazamiento) y zoom en tiempo real.
- **UI Score Info**: En la interfaz, se agregó indicador de coherencia (⚠/✓) al texto del score.

## Mejoras Post-Análisis (00:40)
Basado en el análisis de `analysis_log.txt`:
1. **Filtro de Coherencia**: Si MoodMom y MicroMom se contradicen, sus pesos se reducen a 30% para evitar señales confusas y falsas entradas.
2. **Penalización de Mood Neutro**: Cuando el mood está entre 40-60%, su peso de score se reduce a 30% dado el bajo win rate histórico (33%).
3. **Restricción RSI/Bonus**: Se suma +0.4 al score si RSI < 43 (Win rate observado 86%). Se resta -0.4 al score si RSI > 57.
4. **Cooldown Adaptativo**: El cooldown aumenta de 60s a 120s automáticamente si el bot sufre 2 pérdidas consecutivas.
