import os
import time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

api = IQ_Option(email, password)
api.connect()

print("Prueba de velas BTCUSD")
try:
    c = api.get_candles("BTCUSD", 60, 1, time.time())
    print("BTCUSD ok:", c)
except Exception as e:
    print("Error BTCUSD:", e)

try:
    c = api.get_candles("Bitcoin", 60, 1, time.time())
    print("Bitcoin ok:", c)
except Exception as e:
    print("Error Bitcoin:", e)

try:
    c = api.get_candles("BTCUSD-OTC", 60, 1, time.time())
    print("BTCUSD-OTC ok:", c)
except Exception as e:
    print("Error BTCUSD-OTC:", e)
    
