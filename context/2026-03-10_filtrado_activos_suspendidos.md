# Filtrado Automático de Activos Suspendidos

**Fecha**: 2026-03-10
**Módulos Afectados**: `bot.py`

## 1. Ocultar Activos no Operables
El usuario reportó que al seleccionar ciertos activos del dropdown, el bot informaba que estaban "suspendidos" por IQ Option. Esto generaba confusión al permitir seleccionar pares que no estaban abiertos para trading en ese momento.

**Solución Implementada:**
Se ha refinado la lógica de descubrimiento de activos dentro de `bot.py` (método `run_trading_loop`). 
1. El bot descarga el estado en tiempo real de todos los activos disponibles (`init_v2_data`).
2. Para cada activo, evalúa rigurosamente dos banderas del servidor:
   - `enabled`: Debe ser `True` (indica que el activo existe para el tipo de cuenta).
   - `is_suspended`: Debe ser `False` (indica que el mercado no está en mantenimiento o pausado para ese par).
3. **Resultado**: El Combobox (desplegable) de la interfaz gráfica ahora **solo** muestra los activos que pasan este filtro. Si un activo entra en mantenimiento o se suspende, desaparecerá automáticamente de la lista en el próximo ciclo de actualización, evitando que el usuario intente operar en mercados cerrados.

---

## 2. Compatibilidad con BTC (OTC)
A pesar del filtrado estricto, se mantiene la compatibilidad con el sufijo `-op` para asegurar que Bitcoin y otros pares OTC (que IQ Option marca como abiertos pero con nombre técnico extendido) sigan siendo visibles mientras su bandera de suspensión sea falsa.
