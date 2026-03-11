import streamlit as st
import threading
import queue
import time
import pandas as pd
import datetime
import matplotlib.pyplot as plt
from bot import TradingBot, ACTIVO, MONTO_OPERACION

# Configuración de página
st.set_page_config(page_title="Trading Bot Dashboard", layout="wide", page_icon="📈")

# Estilos personalizados (modo oscuro)
st.markdown("""
    <style>
    .stApp {
        background-color: #1E1E2E;
        color: #CDD6F4;
    }
    </style>
""", unsafe_allow_html=True)

# Inicialización del estado de la sesión
def init_state():
    defaults = {
        'q': queue.Queue(),
        'bot': None,
        'bot_thread': None,
        'is_running': False,
        'logs': [],
        'balance': 0.0,
        'metrics': None,
        'score_details': None,
        'assets': [ACTIVO],
        'orders': {},
        'pnl_wins': 0,
        'pnl_losses': 0,
        'pnl_total': 0.0,
        'cooldown_remaining': 0,
        'countdown': 0,
        'auto_stopped_reason': "",
        'auto_trading': False,
        'interval_val': 3,
        'monto_val': MONTO_OPERACION,
        'activo_val': ACTIVO,
        'trade_markers': [],
        'last_rsi': 50.0
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

def bot_callback(payload):
    st.session_state.q.put(payload)

def start_bot():
    if not st.session_state.is_running:
        st.session_state.logs.append("Iniciando hilo del bot...")
        st.session_state.bot = TradingBot(callback_update=bot_callback)
        st.session_state.bot.monto_operacion = float(st.session_state.monto_val)
        st.session_state.bot.interval = st.session_state.interval_val
        st.session_state.bot.auto_trading = st.session_state.auto_trading
        
        st.session_state.bot_thread = threading.Thread(target=st.session_state.bot.run_trading_loop, daemon=True)
        st.session_state.bot_thread.start()
        st.session_state.is_running = True

def stop_bot():
    if st.session_state.is_running and st.session_state.bot:
        st.session_state.bot.stop()
        st.session_state.logs.append("Se envió señal de detener. Esperando fin del ciclo...")
        st.session_state.is_running = False

def process_queue():
    while not st.session_state.q.empty():
        try:
            payload = st.session_state.q.get_nowait()
            ptype = payload['type']
            
            if ptype == 'status':
                st.session_state.logs.append(payload.get('data', payload.get('msg', '')))
            
            elif ptype == 'balance':
                st.session_state.balance = payload['data']
                
            elif ptype == 'countdown':
                st.session_state.countdown = payload['data']
                
            elif ptype == 'cooldown_remaining':
                st.session_state.cooldown_remaining = payload['data']
                
            elif ptype == 'auto_stopped':
                reason = payload['data']
                st.session_state.auto_trading = False
                st.session_state.auto_stopped_reason = reason
                st.session_state.logs.append(f"⛔ AUTO-TRADING DETENIDO: {reason}")
                
            elif ptype == 'score_details':
                st.session_state.score_details = payload['data']
                
            elif ptype == 'assets':
                st.session_state.assets = payload['data']
                
            elif ptype == 'metrics':
                st.session_state.metrics = payload['data']
                
            elif ptype == 'order':
                d = payload['data']
                oid = str(d['id'])
                if oid not in st.session_state.orders:
                    st.session_state.logs.append(f"Nueva orden detectada: {oid}.")
                    st.session_state.orders[oid] = {
                        'ID': oid, 'Hora': d['time'], 'Dir': d['dir'], 
                        'Inversión': f"${d['amount']}", 'Resultado': d['res'], 'Beneficio': f"${d['prof']:.2f}",
                        'exp_at': d.get('exp_at', 0)
                    }
                    st.session_state.trade_markers.append({
                        'id': oid, 'timestamp': time.time(), 
                        'dir': d['dir'], 'result': None, 'prof': 0
                    })
                    
            elif ptype == 'order_update':
                d = payload['data']
                oid = str(d['id'])
                if oid in st.session_state.orders:
                    st.session_state.orders[oid]['Resultado'] = d['res']
                    st.session_state.orders[oid]['Beneficio'] = f"${d.get('prof', 0):.2f}"
                    
                    for m in st.session_state.trade_markers:
                        if m['id'] == oid:
                            m['result'] = d['res']
                            m['prof'] = d.get('prof', 0)
                            break
                            
                    profit = d.get('prof', 0)
                    if d['res'] == 'WIN':
                        st.session_state.pnl_wins += 1
                    elif d['res'] == 'LOSS':
                        st.session_state.pnl_losses += 1
                    st.session_state.pnl_total += profit
                    
        except queue.Empty:
            break

    # Limitar logs
    if len(st.session_state.logs) > 50:
        st.session_state.logs = st.session_state.logs[-50:]

process_queue()

# --- INTERFAZ GRAFICA ---

# Header
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    st.title("📈 Trading Dashboard")
    status_text = "🟢 EJECUTANDO" if st.session_state.is_running else "🔴 DETENIDO"
    st.subheader(f"Estado: {status_text}")
    
with col2:
    st.metric(label="Balance", value=f"${st.session_state.balance:.2f}")

with col3:
    total_ops = st.session_state.pnl_wins + st.session_state.pnl_losses
    win_rate = (st.session_state.pnl_wins / total_ops * 100) if total_ops > 0 else 0
    st.metric(label="Rentabilidad (PnL)", value=f"${st.session_state.pnl_total:.2f}", 
              delta=f"W:{st.session_state.pnl_wins} | L:{st.session_state.pnl_losses} ({win_rate:.1f}%)")

st.markdown("---")

# Controles
ctrl1, ctrl2, ctrl3 = st.columns(3)
with ctrl1:
    assets = st.session_state.assets
    if st.session_state.activo_val not in assets:
        assets.append(st.session_state.activo_val)
    new_asset = st.selectbox("Divisa Técnica", assets, index=assets.index(st.session_state.activo_val))
    if new_asset != st.session_state.activo_val:
        st.session_state.activo_val = new_asset
        if st.session_state.is_running and st.session_state.bot:
            threading.Thread(target=st.session_state.bot.set_asset, args=(new_asset,), daemon=True).start()
        st.session_state.trade_markers = []
    
    monto = st.number_input("Monto Operación ($)", min_value=1.0, value=float(st.session_state.monto_val))
    if monto != st.session_state.monto_val:
        st.session_state.monto_val = monto
        if st.session_state.bot:
            st.session_state.bot.monto_operacion = float(monto)

with ctrl2:
    intervalo = st.slider("Intervalo de Análisis (seg)", 1, 60, st.session_state.interval_val)
    if intervalo != st.session_state.interval_val:
        st.session_state.interval_val = intervalo
        if st.session_state.bot:
            st.session_state.bot.interval = intervalo
            
    auto = st.checkbox("AUTO-TRADING (Automático)", value=st.session_state.auto_trading)
    if auto != st.session_state.auto_trading:
        st.session_state.auto_trading = auto
        if st.session_state.bot:
            st.session_state.bot.auto_trading = auto
            st.session_state.bot.auto_stopped = False

with ctrl3:
    st.write(f"⏱ Próximo análisis en: {st.session_state.countdown}s")
    if st.session_state.cooldown_remaining > 0:
        st.warning(f"🔒 Cooldown: {st.session_state.cooldown_remaining}s")
    
    if st.session_state.auto_stopped_reason:
        st.error(st.session_state.auto_stopped_reason)

    if not st.session_state.is_running:
        st.button("INICIAR BOT", type="primary", on_click=start_bot, use_container_width=True)
    else:
        st.button("DETENER BOT", type="secondary", on_click=stop_bot, use_container_width=True)

st.markdown("---")

# Métricas y Gráfico
col_metrics, col_chart = st.columns([1, 2])

with col_metrics:
    st.subheader(f"Análisis en Vivo: {st.session_state.activo_val}")
    d = st.session_state.metrics
    sd = st.session_state.score_details
    
    if d and sd:
        st.markdown(f"**Precio:** {d.get('precio', '-')}")
        rsi = d.get('rsi', 50)
        rsi_color = "red" if rsi >= 70 else "green" if rsi <= 30 else "gray"
        st.markdown(f"**RSI (14):** :{rsi_color}[{rsi:.2f}]")
        st.markdown(f"**EMA(20):** {d.get('ema', '-'):.5f} | **SMA(50):** {d.get('sma', '-'):.5f}")
        st.markdown(f"**BB Sup:** {d.get('bb_sup', '-'):.5f} | **BB Inf:** {d.get('bb_inf', '-'):.5f}")
        
        score = sd.get('total', 0)
        score_color = "green" if score >= 0.2 else "red" if score <= -0.2 else "gray"
        st.markdown(f"**Score:** :{score_color}[{score:+.2f}] (µM:{sd.get('micro_momentum',0):+.2f} T:{sd.get('tech',0):+.2f} M:{sd.get('mood_momentum',0):+.2f})")
        
        # Mood
        mood_call = d.get('mood_call', 0.5)
        st.progress(mood_call, text=f"Sentimiento: {int(mood_call*100)}% SUBE / {int((1-mood_call)*100)}% BAJA")
        
        # Condiciones
        with st.expander("Condiciones detalladas"):
            st.write("**Para PUT (Baja):**")
            st.checkbox("RSI >= 70", value=d.get('cond_put_rsi', False), disabled=True)
            st.checkbox("Toca BB Sup", value=d.get('cond_put_bb', False), disabled=True)
            st.checkbox("Tendencia Bajista", value=d.get('cond_put_tend', False), disabled=True)
            
            st.write("**Para CALL (Alza):**")
            st.checkbox("RSI <= 30", value=d.get('cond_call_rsi', False), disabled=True)
            st.checkbox("Toca BB Inf", value=d.get('cond_call_bb', False), disabled=True)
            st.checkbox("Tendencia Alcista", value=d.get('cond_call_tend', False), disabled=True)
    else:
        st.info("Esperando datos...")

with col_chart:
    st.subheader("Gráfico de Mercado")
    d = st.session_state.metrics
    if d and d.get('vela_hist'):
        velas = d['vela_hist']
        fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
        fig.patch.set_facecolor('#1E1E2E')
        ax.set_facecolor('#181825')
        ax.tick_params(colors='#CDD6F4', labelsize=8)
        for spine in ax.spines.values():
            spine.set_edgecolor('#45475A')
            
        x_idx = list(range(len(velas)))
        opens = [v['open'] for v in velas]
        closes = [v['close'] for v in velas]
        highs = [v['max'] for v in velas]
        lows = [v['min'] for v in velas]
        
        colors = ['#A6E3A1' if c >= o else '#F38BA8' for c, o in zip(closes, opens)]
        
        ax.vlines(x_idx, lows, highs, color=colors, linewidth=1)
        
        heights = [abs(c - o) for c, o in zip(closes, opens)]
        bottoms = [min(c, o) for c, o in zip(closes, opens)]
        heights = [h if h > 0 else 0.0001 for h in heights]
        ax.bar(x_idx, heights, bottom=bottoms, color=colors, width=0.7)
        
        # Marcadores
        if st.session_state.trade_markers:
            vela_times = [v.get('from', 0) for v in velas]
            visible_markers = st.session_state.trade_markers[-5:]
            for marker in visible_markers:
                mt = marker['timestamp']
                best_idx = None
                best_diff = float('inf')
                for vi, vt in enumerate(vela_times):
                    diff = abs(vt - mt)
                    if diff < best_diff:
                        best_diff = diff
                        best_idx = vi
                
                if best_idx is not None and best_diff < 30:
                    y_pos = closes[best_idx]
                    res = marker.get('result')
                    if res == 'WIN':
                        ax.plot(best_idx, y_pos, marker='^', color='#A6E3A1', markersize=10, zorder=5)
                    elif res == 'LOSS':
                        ax.plot(best_idx, y_pos, marker='v', color='#F38BA8', markersize=10, zorder=5)
                    elif res is None:
                        ax.plot(best_idx, y_pos, marker='o', color='#F9E2AF', markersize=8, zorder=5)
        
        st.pyplot(fig)
    else:
        st.info("Esperando velas...")

st.markdown("---")

col_logs, col_orders = st.columns(2)

with col_logs:
    st.subheader("Logs del Sistema")
    st.text_area("", value="\n".join(st.session_state.logs), height=200, disabled=True)

with col_orders:
    st.subheader("Historial de Órdenes")
    if st.session_state.orders:
        df = pd.DataFrame(list(st.session_state.orders.values()))
        # Si la orden no ha expirado, calcular el tiempo restante
        now = time.time()
        
        def format_exp(row):
            if row['Resultado'] not in ['WIN', 'LOSS'] and row['exp_at'] > 0:
                rem = row['exp_at'] - now
                if rem > 0:
                    mins = int(rem // 60)
                    secs = int(rem % 60)
                    return f"Expira: {mins:02d}:{secs:02d}"
                return "Cerrando..."
            return row['Resultado']
            
        if 'exp_at' in df.columns:
            df['Resultado'] = df.apply(format_exp, axis=1)
            df = df.drop(columns=['exp_at'])
            
        st.dataframe(df.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("No hay órdenes registradas todavía.")

# Refresco automático mientras corre el bot para actualizar la UI en la nube
if st.session_state.is_running:
    # Retraso e iteración en Streamlit
    time.sleep(1.5)
    st.rerun()
