import os
import json
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
    init_info = api.get_api_option_init_all()
    
    # Init info contains 'result' -> 'turbo' or 'binary' -> 'actives' -> Dictionary of ID: Name
    actives_found = {}
    
    if init_info and "result" in init_info:
        for option_type in ["binary", "turbo"]:
            if option_type in init_info["result"]:
                actives = init_info["result"][option_type].get("actives", {})
                for active_id, active_data in actives.items():
                    name = active_data.get("name")
                    if name:
                        # Map name to ID
                        actives_found[name] = int(active_id)
                        
    print(f"Encontrados {len(actives_found)} activos en el init payload.")
    if "AIG-OTC" in actives_found:
        print(f"ID de AIG-OTC: {actives_found['AIG-OTC']}")
    else:
        print("AIG-OTC no esta en el init info.")
        
    print("Muestra de activos encontrados:", list(actives_found.items())[:10])
else:
    print("Fallo conexion")
