import os
import time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option
import iqoptionapi.constants as OP_code

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

api = IQ_Option(email, password)
check, reason = api.connect()

if check:
    print("Conectado")
    # Buscar como la api obtiene todos los activos
    print("Actives en OP_code: ", list(OP_code.ACTIVES.keys())[:5])
    
    # Try fetching real active list
    all_actives = api.get_all_ACTIVES_OPCODE()
    print("Total activos en get_all_ACTIVES_OPCODE:", len(all_actives) if all_actives else 0)
    
    if all_actives and "AIG-OTC" in all_actives:
        print("AIG-OTC ID:", all_actives["AIG-OTC"])
    else:
        print("No se encontro AIG-OTC en get_all_ACTIVES_OPCODE")

    # Try to see if get_all_open_time contains the ID somewhere?
    # No, get_all_open_time() has "binary" -> "AIG-OTC" -> {"open": True}
    
    print("\nIntento buscar AIG-OTC...")
    # Update local opcode?
    if all_actives:
         OP_code.ACTIVES.update(all_actives)
         print("Actualizado OP_code.ACTIVES localmente")
         
    candles = api.get_candles("AIG-OTC", 60, 10, time.time())
    print("Candles AIG-OTC:", len(candles) if candles else None)
    
else:
    print("Fallo conexion")
