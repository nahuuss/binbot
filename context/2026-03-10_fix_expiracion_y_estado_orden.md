# Fix: Sincronización de Expiración con IQ Option

## Problemas Corregidos

### 1. Cálculo de Expiración Incorrecto
- **Antes**: `time.time() + 60s` — no coincidía con IQ Option.
- **Ahora**: Se usa `get_expiration_time()` de `iqoptionapi.expiration` + `get_server_timestamp()`. 
- Esta función usa la misma lógica que IQ Option:
  - Si quedan >30s en el minuto actual → expira al cierre del próximo minuto
  - Si quedan ≤30s → expira al cierre del minuto después

### 2. Estado de Orden No Actualiza (WIN/LOSS)
- **Antes**: `check_win_v3` era un `while True` sin timeout que nunca retornaba si los datos del websocket no coincidían.
- **Ahora**: Se consulta directamente `api.api.socket_option_closed[order_id]` (misma data que `check_win_v4`) con polling de 1s y timeout de 180s.

### 3. Import de Módulo de Expiración
- Agregado `from iqoptionapi.expiration import get_expiration_time` en `bot.py`.
