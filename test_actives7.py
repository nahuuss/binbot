import os
import json
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

api = IQ_Option(email, password)
check, reason = api.connect()

if check:
    binary_data = api.get_all_init_v2()
    binary_list = ["binary", "turbo"]
    
    missing_actives = {}
    if binary_data:
        for option in binary_list:
            if option in binary_data:
                for actives_id in binary_data[option]["actives"]:
                    active = binary_data[option]["actives"][actives_id]
                    # Format is usually 'tipo.NAME'
                    try:
                        name = str(active["name"]).split(".")[1]
                        missing_actives[name] = int(actives_id)
                    except:
                        pass
                        
    print(f"Total encontrados: {len(missing_actives)}")
    if "AIG-OTC" in missing_actives:
        print(f"EXITO! AIG-OTC ID: {missing_actives['AIG-OTC']}")
    
    # Let's print a few OTCs
    print("Some OTCs:", {k: v for k, v in missing_actives.items() if "OTC" in k})
else:
    print("Fallo conexion")
