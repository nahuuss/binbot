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
    # Method 1
    binary_actives = api.get_ALL_Binary_ACTIVES_OPCODE()
    print("Method 1: get_ALL_Binary_ACTIVES_OPCODE")
    if "AIG-OTC" in binary_actives:
        print(f"Encontrado AIG-OTC: {binary_actives['AIG-OTC']}")
    else:
        print("No encontrado AIG-OTC en Method 1.")
        
    print("\nMethod 2: get_instruments")
    # type can be "turbo-option" or "binary-option" or "crypto"
    instruments, req_id = api.get_instruments("turbo-option")
    print("Turbo options received.")
    for inst in instruments:
        if inst.get("name") == "AIG-OTC":
            print(f"Encontrado AIG-OTC en turbo-option! ID: {inst.get('active_id')}")
            
    instruments2, req_id2 = api.get_instruments("binary-option")
    print("Binary options received.")
    for inst in instruments2:
        if inst.get("name") == "AIG-OTC":
            print(f"Encontrado AIG-OTC en binary-option! ID: {inst.get('active_id')}")

else:
    print("Fallo conexion")
