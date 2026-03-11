# Setup de Entorno y Script de Prueba

## Cambios Realizados
1. **Entorno Virtual**: Se creó un entorno virtual de Python (`.venv`) en la carpeta del proyecto.
2. **Dependencias**: Se instaló la librería no oficial `iqoptionapi` así como `python-dotenv` para el manejo seguro de credenciales.
3. **Variables de Entorno**: Se generó un archivo `.env` vacío (oculto) para que el usuario coloque su `IQ_EMAIL` e `IQ_PASSWORD` sin exponerlos en el código.
4. **Script de Prueba (`test_connection.py`)**: Se creó un primer script de conexión que:
   - Lee las credenciales del `.env`.
   - Intenta el login.
   - Pasa la cuenta a Modo Práctica.
   - Imprime el balance actual.
   - Obtiene y muestra las últimas 5 velas del par EURUSD en temporalidad de 1 minuto, a modo de confirmación de lectura de mercado.

## Estado
Pendiente de prueba por parte del usuario.
