# Solución de Dependencias en Streamlit Cloud (11 de Marzo de 2026)

## Cambio Realizado
Se creó un archivo `requirements.txt` en la raíz del proyecto.

## Razón del Cambio
Al intentar desplegar `app.py` en Streamlit Cloud se produjo el error `ModuleNotFoundError: No module named 'matplotlib'`. Esto sucede debido a que Streamlit Cloud crea un entorno virtual limpio y no sabe qué librerías tiene instaladas tu computadora local.

## Detalles de Implementación
El archivo `requirements.txt` contiene las siguientes dependencias clave que la plataforma instalará automáticamente:
- `streamlit`
- `pandas`
- `matplotlib`
- `python-dotenv`
- `requests`
- `websocket-client`
- `iqoptionapi`

Esto garantizará que al reiniciar o hacer "Reboot" de la aplicación en Streamlit, el entorno de nube descargue e instale todas las herramientas gráficas y de conectividad requeridas.
