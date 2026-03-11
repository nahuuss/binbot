# Implementación de Múltiples Indicadores Técnicos y Consenso

El bot original evaluaba únicamente el RSI para realizar operaciones. Según lo solicitado, se ha modificado `bot.py` para calcular e integrar múltiples métodos simultáneamente con el fin de generar señales mucho más precisas y seguras.

## Indicadores Agregados
Se crearon funciones matemáticas puras (sin depender de más librerías) para calcular:
- **SMA (Media Móvil Simple) de 50 periodos**: Ayuda a visualizar la tendencia general a largo plazo (dentro de la temporalidad analizada).
- **EMA (Media Móvil Exponencial) de 20 periodos**: Sigue el precio más de cerca, reacciona más rápido a los cambios de corto plazo.
- **Bandas de Bollinger (20 periodos, desv. est 2.0)**: Miden la volatilidad y muestran los niveles estadísticos donde el precio podría estar "caro" (banda superior) o "barato" (banda inferior).

## Nueva Lógica de Trading (Consenso)
En vez de operar a ciegas cuando el RSI cruza sus límites, ahora el bot requiere que **todos** los indicadores estén de acuerdo (Consenso Técnico) antes de arriesgar dinero en una binaria.

**Para VENDER (Put / Baja):**
1. RSI superior o igual a 70 (Sobrecompra).
2. El Precio Actual está tocando o rompiendo la Banda de Bollinger Superior.
3. La tendencia macro está marcando fuerza bajista (EMA20 < SMA50).

**Para COMPRAR (Call / Sube):**
1. RSI inferior o igual a 30 (Sobreventa).
2. El Precio Actual está tocando o rompiendo la Banda de Bollinger Inferior.
3. La tendencia macro está marcando fuerza alcista (EMA20 > SMA50).

Con estas verificaciones, se filtran enormemente las "señales falsas" y el bot se vuelve mucho más selectivo y robusto al momento de operar con Bitcoin o cualquier otro activo.
Además, los valores de los cálculos (Precios y cada indicador) se irán imprimiendo en pantalla por cada vela analizada para llevar un control visual exacto de qué ve el bot.
