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
    print("\nMethod 2: get_instruments")
    instruments = api.get_instruments("turbo-option")
    if type(instruments) == dict and "message" in instruments:
        data = instruments["message"]
        print("Type of data:", type(data))
        if type(data) == str:
            print("Data str snippet:", data[:100])
        elif type(data) == dict or type(data) == list:
            print("Data es dict/list")
else:
    print("Fallo conexion")
