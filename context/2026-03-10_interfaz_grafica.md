# Implementación de Interfaz Gráfica (GUI) para el Bot

El día de hoy se completó una refactorización mayor del bot y la adición de un Dashboard visual en Tkinter.

### Cambios en `bot.py`
Se transformó el código procedimental en una Clase (`TradingBot`). El bucle principal pasó a ser un método `run_trading_loop()`. Esto fue necesario para poder empaquetar de forma segura el bucle infinito y meterlo dentro de un hilo secundario (Threading) sin congelar la interfaz principal. 
También se añadió un método `_emit` por el cual el bot puede enviarle sus cálculos matemáticos a la ventana principal usando diccionarios a través de una función Callback.

### Creación de `gui.py`
Se creó el archivo que levanta la ventana. Esta interfaz posee:
- **Tema Oscuro**: Colores modernos usando estilos de Catppuccin Macchiato.
- **Panel Izquierdo**:
  - `Análisis en vivo`: Muestra el valor de precio, RSI (cambia de color según sobreventa/sobrecompra) y Medias móviles.
  - `Strikes`: Muestra un Checkbox visual (círculos) por cada una de las 6 condiciones de la estrategia matemática que deben cumplirse. Se encienden en verde en tiempo real.
  - Controles de INICIAR y DETENER bot seguros (matan el hilo).
- **Panel Derecho**:
  - Caja de texto para todos los mensajes del Logger del bot en tiempo real.
  - Grilla (`Treeview`) para mostrar el historial de operaciones ejecutadas, actualizando el resultado (Win/Loss/Tie) según vayan venciendo sus expiraciones.

Con esto, el usuario ya no necesita ver una consola de comandos negra, usando el UI tiene total visibilidad de "qué le falta al bot" para lanzar una operación.
