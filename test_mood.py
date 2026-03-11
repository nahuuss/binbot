import os
import time
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

api = IQ_Option(email, password)
check, reason = api.connect()

if check:
    print("Conectado")
    
    asset = "BTCUSD"
    print(f"Iniciando mood stream para {asset}...")
    api.start_mood_stream(asset, "turbo-option")
    
    for i in range(5):
        mood = api.get_traders_mood(asset)
        print(f"[{i}] Traders Mood: {mood} (Representa la % de opciones CALL/Sube)")
        time.sleep(1)
        
    print("Deteniendo stream...")
    api.stop_mood_stream(asset, "turbo-option")
else:
    print("Error conectando:", reason)
