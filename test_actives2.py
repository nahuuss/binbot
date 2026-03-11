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
    op_data = api.get_all_open_time()
    if "binary" in op_data and "AIG-OTC" in op_data["binary"]:
        print("Data de AIG-OTC en binary:")
        print(json.dumps(op_data["binary"]["AIG-OTC"], indent=2))
        
    print("\n--- buscando en el init data ---")
    data = api.get_profile_ansyc()
    # sometimes there is an active list in init data?
    
else:
    print("Fallo")
