import os
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
email = os.getenv("IQ_EMAIL")
password = os.getenv("IQ_PASSWORD")

api = IQ_Option(email, password)
check, reason = api.connect()

if check:
    print("Conectado")
    import time
    end_time = int(time.time())
    
    print("Intentando get_position_history_v2('binary-option', 10, 0, end_time, 0)")
    # get_position_history_v2(instrument_type, limit, offset, end, start)
    hist = api.get_position_history_v2("binary-option", 10, 0, end_time, 0)
    
    if hist and hist[0]:
        print("BINARY HIST:", len(hist[1].get("positions", [])))
        for p in hist[1].get("positions", []):
            print(p.get("id"), p.get("instrument_dir"), p.get("invest"), p.get("close_profit"))
        
    hist_turbo = api.get_position_history_v2("turbo-option", 10, 0, end_time, 0)
    if hist_turbo and hist_turbo[0]:
        print("TURBO HIST:", len(hist_turbo[1].get("positions", [])))
        for p in hist_turbo[1].get("positions", []):
            print(p.get("id"), p.get("instrument_dir"), p.get("invest"), p.get("close_profit"))
        
else:
    print("Error:", reason)
