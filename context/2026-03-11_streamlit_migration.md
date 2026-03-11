# Migración a Streamlit (11 de Marzo de 2026)

## Cambio Realizado
Se ha creado el archivo `app.py` para actuar como el panel gráfico web en reemplazo de `gui.py`.

## Razón del Cambio
La plataforma Streamlit Cloud se ejecuta en servidores remotos "headless" (es decir, sin un entorno de escritorio). El uso de librerías como `tkinter` (utilizada en `gui.py`) intentaba abrir ventanas de escritorio, lo cual provoca un error de incompatibilidad que detiene la ejecución ("ImportError: This app has encountered an error... _tkinter"). 

Para solucionar este error y permitir la publicación en la web, se construyó una nueva interfaz exclusivamente mediante comandos de la librería `streamlit`.

## Detalles de Implementación
- Se migró toda la lógica de visualización que utilizaba Tkinter a utilizar la API de layout de Streamlit (`st.columns`, `st.metric`, `st.dataframe`).
- El soporte para las operaciones en un hilo secundario (`TradingBot`) se adaptó utilizando un sistema de colas sincronizado con `st.session_state` para evitar que se pierdan los datos entre refrescos de página de Streamlit.
- Los gráficos con velas japonesas generados en Matplotlib fueron envueltos en `st.pyplot(fig)` para que pudiesen graficarse correctamente en la página web.
- El ciclo de refresco periódico se manejó añadiendo un comando de `st.rerun()` cada 1.5 segundos si el bot se encuentra marcado como activo, posibilitando una experiencia "en vivo" analógica a `root.after_loop()`.

## Ejecución
A partir de ahora, ejecutar en modo web:
```bash
streamlit run app.py
```
**(En Streamlit Cloud se debe seleccionar `app.py` como el punto de entrada principal en lugar de gui.py)**
