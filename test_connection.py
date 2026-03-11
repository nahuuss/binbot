import os
import time
import logging
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

# Configurar logging para ver errores si los hay
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def main():
    # Cargar variables de entorno
    load_dotenv()
    
    email = os.getenv("IQ_EMAIL")
    password = os.getenv("IQ_PASSWORD")
    
    if not email or not password or email == "tu_correo@ejemplo.com":
        logging.error("Por favor, configura tu email y contraseña en el archivo .env")
        return

    logging.info("Intentando conectar a IQ Option...")
    api = IQ_Option(email, password)
    
    # Intentar conexión
    check, reason = api.connect()
    
    if check:
        logging.info("¡Conexión exitosa!")
        
        # Cambiar a cuenta de práctica
        api.change_balance("PRACTICE")
        balance = api.get_balance()
        logging.info(f"Balance de Práctica: ${balance}")
        
        # Probar leer velas de EURUSD (1 minuto)
        logging.info("Obteniendo últimas 5 velas de EURUSD de 1 minuto...")
        candles = api.get_candles("EURUSD", 60, 5, time.time())
        for c in candles:
            logging.info(f"Vela: Apertura={c['open']}, Cierre={c['close']}, Max={c['max']}, Min={c['min']}")
            
    else:
        logging.error(f"Fallo al conectar. Razón: {reason}")
        
if __name__ == "__main__":
    main()
