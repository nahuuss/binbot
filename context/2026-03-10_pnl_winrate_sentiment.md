# Mejoras: Sentiment Strikes, PnL Counter y Win Rate

## Cambios

### 1. Sentimiento en Condiciones (Strikes)
- **PUT**: "Sentimiento BAJA (Mood < 45%)" → se ilumina cuando el mood está a favor de baja
- **CALL**: "Sentimiento SUBE (Mood > 55%)" → se ilumina cuando el mood está a favor de sube

### 2. Contador de Ganancia/Pérdida (PnL) en Header
- `W:X` = Wins | `L:X` = Losses | `XX%` = Win Rate | `P/L: $X.XX` = Beneficio neto
- Color verde si ganancia positiva, rojo si negativa

### 3. Intervalo por Defecto Reducido
- De 10s a 3s para una actualización más rápida de condiciones

### 4. Ventana Maximizada
- Se adapta automáticamente al tamaño de la pantalla del usuario
