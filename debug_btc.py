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
    data = api.get_all_init_v2()
    with open("init_v2_dump.json", "w") as f:
        json.dump(data, f, indent=4)
    
    print("Keys in init_v2:", data.keys())
    
    found_btc = []
    for category in data:
        if isinstance(data[category], dict) and "actives" in data[category]:
            for aid in data[category]["actives"]:
                act = data[category]["actives"][aid]
                if "BTC" in str(act.get("name", "")):
                    found_btc.append({
                        "id": aid,
                        "category": category,
                        "name": act.get("name"),
                        "enabled": act.get("enabled"),
                        "suspended": act.get("is_suspended")
                    })
    
    print("\nAssets found with 'BTC':")
    for item in found_btc:
        print(item)
else:
    print("Failed to connect")
