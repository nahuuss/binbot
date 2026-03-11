import tkinter as tk
from tkinter import ttk
import threading
import queue
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import collections
import sys
from bot import TradingBot, ACTIVO, MONTO_OPERACION

class BotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("IQ Option Trading Bot Dashboard")
        
        # Auto-detectar tamaño de pantalla y adaptar
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        self.root.state('zoomed')  # Maximizar en Windows
        
        self.root.configure(bg="#1E1E2E")
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.q = queue.Queue()
        self.bot = None
        self.bot_thread = None
        self.is_closing = False
        self.exp_tracker = {} # Diccionario para rastrear {order_id: timestamp_expiracion}
        self.pnl_wins = 0
        self.pnl_losses = 0
        self.pnl_total = 0.0
        self.trade_markers = []  # Lista de {timestamp, price, result} para marcar en el gráfico
        self._cooldown_remaining = 0
        self._last_rsi = 50.0

        self.setup_ui()
        self.root.after(100, self.process_queue)
        self.root.after(1000, self.update_order_timers) # Iniciar contador de órdenes
        self.root.after(500, self.start_bot)  # Botón Iniciar automático
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1E1E2E")
        style.configure("TLabel", background="#1E1E2E", foreground="#CDD6F4", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#89B4FA")
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=5)
        
        # --- HEADER ---
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=15, pady=10)
        
        ttk.Label(header_frame, text=f"Trading Dashboard", style="Header.TLabel").pack(side=tk.LEFT)
        self.lbl_status = ttk.Label(header_frame, text="Estado: DETENIDO", foreground="#F38BA8", font=("Segoe UI", 10, "bold"))
        self.lbl_status.pack(side=tk.RIGHT)
        
        self.lbl_balance = ttk.Label(header_frame, text="Balance: $0.00", foreground="#A6E3A1", font=("Segoe UI", 12, "bold"))
        self.lbl_balance.pack(side=tk.RIGHT, padx=20)
        
        # PnL Counter en header
        self.lbl_pnl = ttk.Label(header_frame, text="W:0 | L:0 | P/L: $0.00", foreground="#CDD6F4", font=("Segoe UI", 10, "bold"))
        self.lbl_pnl.pack(side=tk.RIGHT, padx=15)
        
        # --- CONTENT (Panels) ---
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        
        # Left Panel: Metrics & Conditions
        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, expand=False, padx=(0, 10))
        
        # Metrics Group
        self.lf_metrics = tk.LabelFrame(left_panel, text=f" Análisis en Vivo ({ACTIVO}) ", bg="#1E1E2E", fg="#89B4FA", font=("Segoe UI", 10, "bold"))
        self.lf_metrics.pack(fill=tk.X, pady=(0, 10), ipady=5, ipadx=5)
        
        self.lbl_precio = ttk.Label(self.lf_metrics, text="Precio: -")
        self.lbl_precio.pack(anchor=tk.W, pady=2)
        self.lbl_rsi = ttk.Label(self.lf_metrics, text="RSI (14): -")
        self.lbl_rsi.pack(anchor=tk.W, pady=2)
        self.lbl_ema_sma = ttk.Label(self.lf_metrics, text="EMA(20) / SMA(50): - / -")
        self.lbl_ema_sma.pack(anchor=tk.W, pady=2)
        self.lbl_bb = ttk.Label(self.lf_metrics, text="BB(Sup / Inf): - / -")
        self.lbl_bb.pack(anchor=tk.W, pady=2)
        self.lbl_score = ttk.Label(self.lf_metrics, text="Score: - (esperando datos...)", font=("Segoe UI", 9, "bold"))
        self.lbl_score.pack(anchor=tk.W, pady=2)
        
        # Strikes Group
        lf_strikes = tk.LabelFrame(left_panel, text=" Condiciones (Strikes) ", bg="#1E1E2E", fg="#89B4FA", font=("Segoe UI", 10, "bold"))
        lf_strikes.pack(fill=tk.X, pady=(0, 10), ipady=5, ipadx=5)
        
        ttk.Label(lf_strikes, text="Para operación a la BAJA (Put):").pack(anchor=tk.W, pady=(5,0))
        self.c_put_rsi = self.create_strike(lf_strikes, "RSI >= 70 (Sobrecompra)")
        self.c_put_bb = self.create_strike(lf_strikes, "Precio tocando BB Superior")
        self.c_put_tend = self.create_strike(lf_strikes, "Tendencia Bajista (EMA < SMA)")
        self.c_put_mood = self.create_strike(lf_strikes, "Sentimiento BAJA (Mood < 45%)")
        
        ttk.Label(lf_strikes, text="Para operación al ALZA (Call):").pack(anchor=tk.W, pady=(10,0))
        self.c_call_rsi = self.create_strike(lf_strikes, "RSI <= 30 (Sobreventa)")
        self.c_call_bb = self.create_strike(lf_strikes, "Precio tocando BB Inferior")
        self.c_call_tend = self.create_strike(lf_strikes, "Tendencia Alcista (EMA > SMA)")
        self.c_call_mood = self.create_strike(lf_strikes, "Sentimiento SUBE (Mood > 55%)")

        # Interpretation Panel
        lf_interp = tk.LabelFrame(left_panel, text=" ¿Qué analiza el bot? ", bg="#1E1E2E", fg="#89B4FA", font=("Segoe UI", 10, "bold"))
        lf_interp.pack(fill=tk.X, pady=(0, 10), ipady=4, ipadx=5)

        self.lbl_interp_estado = tk.Label(lf_interp, text="Esperando datos...", bg="#1E1E2E",
                                          fg="#6C7086", font=("Segoe UI", 11, "bold"), anchor=tk.W)
        self.lbl_interp_estado.pack(fill=tk.X, padx=5, pady=(4, 2))

        # Barra de score visual: PUT ←——[■]——→ CALL
        score_row = tk.Frame(lf_interp, bg="#1E1E2E")
        score_row.pack(fill=tk.X, padx=5, pady=2)
        tk.Label(score_row, text="PUT", bg="#1E1E2E", fg="#F38BA8", font=("Segoe UI", 7, "bold")).pack(side=tk.LEFT)
        self.canvas_score_bar = tk.Canvas(score_row, height=10, bg="#2A2A3E", highlightthickness=0)
        self.canvas_score_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        tk.Label(score_row, text="CALL", bg="#1E1E2E", fg="#A6E3A1", font=("Segoe UI", 7, "bold")).pack(side=tk.LEFT)

        self.lbl_interp_factor = tk.Label(lf_interp, text="", bg="#1E1E2E", fg="#CDD6F4",
                                          font=("Segoe UI", 9), anchor=tk.W, wraplength=240, justify=tk.LEFT)
        self.lbl_interp_factor.pack(fill=tk.X, padx=5, pady=1)

        self.lbl_interp_next = tk.Label(lf_interp, text="", bg="#1E1E2E", fg="#94E2D5",
                                        font=("Segoe UI", 9), anchor=tk.W, wraplength=240, justify=tk.LEFT)
        self.lbl_interp_next.pack(fill=tk.X, padx=5, pady=(1, 4))

        # Controls
        controls = ttk.Frame(left_panel)
        controls.pack(fill=tk.X, pady=10)
        
        self.lbl_interval = ttk.Label(controls, text="Intervalo de Análisis: 10s")
        self.lbl_interval.pack(anchor=tk.W)
        
        self.scale_interval = ttk.Scale(controls, from_=1, to_=60, orient=tk.HORIZONTAL, command=self.on_interval_change)
        self.scale_interval.set(3)
        self.scale_interval.pack(fill=tk.X, pady=(0, 5))
        
        self.lbl_countdown = ttk.Label(controls, text="Próximo análisis en: --", foreground="#F9E2AF", font=("Segoe UI", 10, "bold"))
        self.lbl_countdown.pack(anchor=tk.W, pady=(0, 10))
        
        btns_frame = ttk.Frame(controls)
        btns_frame.pack(fill=tk.X)
        
        self.btn_start = tk.Button(btns_frame, text="INICIAR BOT", bg="#A6E3A1", fg="#11111B", font=("Segoe UI", 11, "bold"), command=self.start_bot)
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
        
        self.btn_stop = tk.Button(btns_frame, text="DETENER BOT", bg="#F38BA8", fg="#11111B", font=("Segoe UI", 11, "bold"), state=tk.DISABLED, command=self.stop_bot)
        self.btn_stop.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5,0))
        
        # Asset Selection
        asset_frame = ttk.Frame(controls)
        asset_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(asset_frame, text="Divisa Técnica:").pack(side=tk.LEFT)
        self.cb_asset = ttk.Combobox(asset_frame, values=["BTCUSD", "BTCUSD-OTC", "EURUSD", "EURUSD-OTC", "ETHUSD", "ETHUSD-OTC"], state="readonly", width=20, height=15)
        self.cb_asset.set(ACTIVO)
        self.cb_asset.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        self.cb_asset.bind("<<ComboboxSelected>>", self.on_asset_change)
        
        # Investment Amount Selection
        amount_frame = ttk.Frame(controls)
        amount_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(amount_frame, text="Monto Operación ($):").pack(side=tk.LEFT)
        self.sv_amount = tk.StringVar(value=str(MONTO_OPERACION))
        self.sp_amount = ttk.Spinbox(amount_frame, from_=1, to=1000, textvariable=self.sv_amount, width=10, command=self.on_amount_change)
        self.sp_amount.pack(side=tk.RIGHT)
        self.sp_amount.bind("<KeyRelease>", lambda e: self.on_amount_change())
        
        # Auto Trading Toggle
        auto_frame = ttk.Frame(controls)
        auto_frame.pack(fill=tk.X, pady=(10, 0))
        self.auto_var = tk.BooleanVar(value=False)
        self.chk_auto = tk.Checkbutton(
            auto_frame, text="  AUTO-TRADING (Operar Automáticamente)",
            variable=self.auto_var, command=self.on_auto_toggle,
            bg="#1E1E2E", fg="#F9E2AF", selectcolor="#313244",
            activebackground="#1E1E2E", activeforeground="#F9E2AF",
            font=("Segoe UI", 10, "bold"), anchor=tk.W
        )
        self.chk_auto.pack(fill=tk.X, pady=5)
        
        # Auto-trade timer label
        self.lbl_auto_timer = ttk.Label(auto_frame, text="", foreground="#94E2D5", font=("Segoe UI", 9))
        self.lbl_auto_timer.pack(anchor=tk.W)
        
        # Right Panel: Logs and History
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Frame for Chart + Mood Widget
        chart_mood_frame = ttk.Frame(right_panel)
        chart_mood_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Traders Mood Widget (Left side)
        self.mood_frame = tk.Frame(chart_mood_frame, bg="#181825", width=45)
        self.mood_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.mood_frame.pack_propagate(False)
        
        self.lbl_mood_up = tk.Label(self.mood_frame, text="SUBE\n50%", bg="#181825", fg="#A6E3A1", font=("Segoe UI", 9, "bold"))
        self.lbl_mood_up.pack(side=tk.TOP, pady=5)
        
        self.canvas_mood = tk.Canvas(self.mood_frame, width=15, bg="#181825", highlightthickness=0)
        self.canvas_mood.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=5)
        
        self.lbl_mood_down = tk.Label(self.mood_frame, text="BAJA\n50%", bg="#181825", fg="#F38BA8", font=("Segoe UI", 9, "bold"))
        self.lbl_mood_down.pack(side=tk.BOTTOM, pady=5)
        
        # Live Chart Section (Upper Right)
        self.fig, self.ax = plt.subplots(figsize=(6, 3), dpi=100)
        self.fig.patch.set_facecolor('#1E1E2E')
        self.ax.set_facecolor('#181825')
        self.ax.tick_params(colors='#CDD6F4', labelsize=8)
        for spine in self.ax.spines.values():
            spine.set_edgecolor('#45475A')
            
        chart_right_col = tk.Frame(chart_mood_frame, bg="#1E1E2E")
        chart_right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_right_col)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Toolbar personalizada con estilo dark
        nav_bar = tk.Frame(chart_right_col, bg="#181825", pady=2)
        nav_bar.pack(side=tk.TOP, fill=tk.X)

        self.toolbar = NavigationToolbar2Tk(self.canvas, chart_right_col)
        self.toolbar.pack_forget()  # Ocultar toolbar original

        _btn_style = dict(bg="#2A2A3E", fg="#CDD6F4", activebackground="#45475A",
                          activeforeground="#CDD6F4", relief=tk.FLAT, borderwidth=0,
                          font=("Segoe UI", 9), padx=8, pady=3, cursor="hand2")

        tk.Button(nav_bar, text="⌂ Home",   command=self.toolbar.home,    **_btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_bar, text="◀ Atrás",  command=self.toolbar.back,    **_btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_bar, text="Adelante ▶", command=self.toolbar.forward, **_btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_bar, text="✥ Pan",    command=self.toolbar.pan,     **_btn_style).pack(side=tk.LEFT, padx=2)
        tk.Button(nav_bar, text="⊕ Zoom",   command=self.toolbar.zoom,    **_btn_style).pack(side=tk.LEFT, padx=2)
        # Console Log Text Box
        self.log_text = tk.Text(right_panel, height=6, bg="#181825", fg="#CDD6F4", font=("Consolas", 9), state=tk.DISABLED)
        self.log_text.pack(fill=tk.X, pady=(0, 10))
        
        # History Table
        columns = ('id', 'time', 'dir', 'amount', 'res', 'prof')
        self.tree = ttk.Treeview(right_panel, columns=columns, show='headings', height=6)
        self.tree.heading('id', text='ID Orden')
        self.tree.heading('time', text='Hora')
        self.tree.heading('dir', text='Dirección')
        self.tree.heading('amount', text='Inversión')
        self.tree.heading('res', text='Resultado')
        self.tree.heading('prof', text='Beneficio')
        
        self.tree.column('id', width=80)
        self.tree.column('time', width=80)
        self.tree.column('dir', width=80)
        self.tree.column('amount', width=80)
        self.tree.column('res', width=80)
        self.tree.column('prof', width=80)
        
        self.tree.pack(fill=tk.BOTH, expand=True)

    def create_strike(self, parent, text):
        f = ttk.Frame(parent)
        f.pack(fill=tk.X, pady=2, padx=10)
        indicator = tk.Label(f, text="●", fg="#45475A", bg="#1E1E2E", font=("Segoe UI", 10))
        indicator.pack(side=tk.LEFT, padx=(0,5))
        ttk.Label(f, text=text).pack(side=tk.LEFT)
        return indicator

    def update_strike(self, indicator, is_active):
        color = "#A6E3A1" if is_active else "#45475A" # Verde o Gris oscuro
        indicator.config(fg=color)

    def on_interval_change(self, val):
        i_val = int(float(val))
        self.lbl_interval.config(text=f"Intervalo de Análisis: {i_val}s")
        if self.bot:
            self.bot.interval = i_val

    def bot_callback(self, payload):
        # Envía datos del hilo del bot a la cola (Thread safe)
        self.q.put(payload)

    def process_queue(self):
        if self.is_closing:
            return
            
        try:
            while True:
                payload = self.q.get_nowait()
                ptype = payload['type']
                try:
                    if ptype == 'status':
                        self.append_log(payload.get('data', payload.get('msg', '')))
                        
                    elif ptype == 'balance':
                        self.lbl_balance.config(text=f"Balance: ${payload['data']:.2f}")
                        
                    elif ptype == 'countdown':
                        secs = payload['data']
                        self.lbl_countdown.config(text=f"Próximo análisis en: {secs}s")
                        if self.auto_var.get():
                            self.lbl_auto_timer.config(text=f"⏱ Auto-trade analiza en: {secs}s")
                        
                    elif ptype == 'cooldown_remaining':
                        rem = payload['data']
                        self._cooldown_remaining = rem
                        if rem > 0 and self.auto_var.get():
                            self.lbl_auto_timer.config(text=f"🔒 Cooldown: {rem}s (esperando para operar)")
                        elif self.auto_var.get():
                            self.lbl_auto_timer.config(text=f"✅ Auto-trade listo para operar")
                    
                    elif ptype == 'auto_stopped':
                        reason = payload['data']
                        self.auto_var.set(False)
                        self.lbl_auto_timer.config(text=f"⛔ {reason} - Auto-trading detenido", foreground="#F38BA8")
                        self.append_log(f"⛔ AUTO-TRADING DETENIDO: {reason}")
                    
                    elif ptype == 'score_details':
                        sd = payload['data']
                        score = sd['total']
                        coh = "⚠" if sd.get('coherence', 0) else "✓"
                        if score >= 0.20:
                            sc_color = "#A6E3A1"
                            sc_dir = "CALL ↑"
                        elif score <= -0.20:
                            sc_color = "#F38BA8"
                            sc_dir = "PUT ↓"
                        else:
                            sc_color = "#6C7086"
                            sc_dir = "HOLD ─"
                        self.lbl_score.config(
                            text=f"Score: {score:+.2f} [{sc_dir}] {coh} | µM:{sd['micro_momentum']:+.2f} T:{sd['tech']:+.2f} M:{sd['mood_momentum']:+.2f}",
                            foreground=sc_color
                        )
                        self._update_interpretation(sd)
                        
                    elif ptype == 'assets':
                        open_assets = payload['data']
                        if open_assets:
                            self.cb_asset['values'] = open_assets
                            self.append_log(f"Cargados {len(open_assets)} activos disponibles.")
                            # Si el activo actual no está en la lista de abiertos, forzar cambio al primero
                            if self.bot and self.bot.current_asset not in open_assets:
                                self.cb_asset.set(open_assets[0])
                                self.on_asset_change(None)
                                
                    elif ptype == 'metrics':
                        d = payload['data']
                        self.lbl_precio.config(text=f"Precio: {d['precio']}")
                        
                        # Generar Gráfico de Velas Japonesas (5s timeframe)
                        velas = d.get('vela_hist', [])
                        if velas:
                            self.ax.clear()
                            # Restaurar estilo de fondo y ejes tras el clear()
                            self.ax.set_facecolor('#181825')
                            self.ax.tick_params(colors='#CDD6F4', labelsize=7)
                            for spine in self.ax.spines.values():
                                spine.set_edgecolor('#45475A')
                                
                            x_idx = list(range(len(velas)))
                            opens = [v['open'] for v in velas]
                            closes = [v['close'] for v in velas]
                            highs = [v['max'] for v in velas]
                            lows = [v['min'] for v in velas]
                            
                            # Colores: Verde (Sube) - Rojo (Baja)
                            colors = ['#A6E3A1' if c >= o else '#F38BA8' for c, o in zip(closes, opens)]
                            
                            # Mechas
                            self.ax.vlines(x_idx, lows, highs, color=colors, linewidth=0.8)
                            
                            # Cuerpos
                            heights = [abs(c - o) for c, o in zip(closes, opens)]
                            bottoms = [min(c, o) for c, o in zip(closes, opens)]
                            heights = [h if h > 0 else 0.0001 for h in heights]
                            
                            self.ax.bar(x_idx, heights, bottom=bottoms, color=colors, width=0.7)
                            
                            # Etiquetas de tiempo en eje X (cada ~12 velas = ~1 min)
                            from datetime import datetime as dt
                            tick_positions = []
                            tick_labels = []
                            step = max(1, len(velas) // 6)  # ~6 etiquetas en total
                            for i in range(0, len(velas), step):
                                ts = velas[i].get('from', 0)
                                if ts:
                                    tick_positions.append(i)
                                    tick_labels.append(dt.fromtimestamp(ts).strftime('%H:%M:%S'))
                            self.ax.set_xticks(tick_positions)
                            self.ax.set_xticklabels(tick_labels, rotation=30, ha='right')
                            
                            # Ajuste visual límites (padding Y)
                            min_p, max_p = min(lows), max(highs)
                            margen = (max_p - min_p) * 0.1 if max_p > min_p else 0.01
                            self.ax.set_ylim(min_p - margen, max_p + margen)
                            
                            # === MARCADORES DE TRADES (solo últimos 5) ===
                            if self.trade_markers and velas:
                                vela_times = [v.get('from', 0) for v in velas]
                                # Solo mostrar los últimos 5 marcadores
                                visible_markers = self.trade_markers[-5:]
                                for mi, marker in enumerate(visible_markers):
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
                                        # Stagger offset para evitar superposición
                                        y_offset = 14 + (mi % 3) * 10
                                        if res == 'WIN':
                                            self.ax.plot(best_idx, y_pos, marker='^', color='#A6E3A1', markersize=8, zorder=5)
                                            self.ax.annotate(f"+${marker['prof']:.2f}", (best_idx, y_pos), 
                                                textcoords="offset points", xytext=(0, y_offset), 
                                                fontsize=6, color='#A6E3A1', ha='center', fontweight='bold',
                                                bbox=dict(boxstyle='round,pad=0.2', fc='#1E1E2E', ec='#A6E3A1', alpha=0.8))
                                        elif res == 'LOSS':
                                            self.ax.plot(best_idx, y_pos, marker='v', color='#F38BA8', markersize=8, zorder=5)
                                            self.ax.annotate(f"-${abs(marker['prof']):.2f}", (best_idx, y_pos), 
                                                textcoords="offset points", xytext=(0, -(y_offset)), 
                                                fontsize=6, color='#F38BA8', ha='center', fontweight='bold',
                                                bbox=dict(boxstyle='round,pad=0.2', fc='#1E1E2E', ec='#F38BA8', alpha=0.8))
                                        elif res is None:
                                            self.ax.plot(best_idx, y_pos, marker='o', color='#F9E2AF', markersize=6, zorder=5)
                                
                                # Limitar historial total de marcadores
                                if len(self.trade_markers) > 20:
                                    self.trade_markers = self.trade_markers[-20:]
                            
                            self.canvas.draw()
                        
                        # Color rojo si >70, verde si <30
                        self._last_rsi = d['rsi']
                        rsi_color = "#F38BA8" if d['rsi']>=70 else "#A6E3A1" if d['rsi']<=30 else "#CDD6F4"
                        self.lbl_rsi.config(text=f"RSI (14): {d['rsi']:.2f}", foreground=rsi_color)
                        
                        self.lbl_ema_sma.config(text=f"EMA(20): {d['ema']:.5f}  |  SMA(50): {d['sma']:.5f}")
                        self.lbl_bb.config(text=f"BB Sup: {d['bb_sup']:.5f}  |  BB Inf: {d['bb_inf']:.5f}")
                        
                        # Actualizar Widget Traders Mood
                        mood_call = d.get('mood_call', 0.5)
                        mood_put = 1.0 - mood_call
                        
                        self.lbl_mood_up.config(text=f"SUBE\n{int(mood_call * 100)}%")
                        self.lbl_mood_down.config(text=f"BAJA\n{int(mood_put * 100)}%")
                        
                        self.canvas_mood.delete("all")
                        self.canvas_mood.update_idletasks()
                        h = self.canvas_mood.winfo_height()
                        w = self.canvas_mood.winfo_width()
                        
                        if h > 10:
                            # Dibujar barra CALL (Sube) - Arriba (Verde)
                            self.canvas_mood.create_rectangle(0, 0, w, h * mood_call, fill="#A6E3A1", outline="")
                            # Dibujar barra PUT (Baja) - Abajo (Roja)
                            self.canvas_mood.create_rectangle(0, h * mood_call, w, h, fill="#F38BA8", outline="")
                        
                        # Actualizar UI de Strikes
                        self.update_strike(self.c_put_rsi, d['cond_put_rsi'])
                        self.update_strike(self.c_put_bb, d['cond_put_bb'])
                        self.update_strike(self.c_put_tend, d['cond_put_tend'])
                        self.update_strike(self.c_put_mood, d.get('cond_put_mood', False))
                        
                        self.update_strike(self.c_call_rsi, d['cond_call_rsi'])
                        self.update_strike(self.c_call_bb, d['cond_call_bb'])
                        self.update_strike(self.c_call_tend, d['cond_call_tend'])
                        self.update_strike(self.c_call_mood, d.get('cond_call_mood', False))
                        
                    elif ptype == 'order':
                        d = payload['data']
                        oid = str(d['id'])
                        if not self.tree.exists(oid):
                            self.append_log(f"Nueva orden detectada: {oid}. Expiración: {d.get('exp_at', 'N/A')}")
                            self.tree.insert('', tk.END, iid=oid, values=(d['id'], d['time'], d['dir'], f"${d['amount']}", d['res'], f"${d['prof']:.2f}"))
                            if d.get('exp_at'):
                                self.exp_tracker[oid] = d['exp_at']
                            # Guardar marcador para el gráfico
                            import time as _time
                            self.trade_markers.append({
                                'id': oid, 'timestamp': _time.time(), 
                                'dir': d['dir'], 'result': None, 'prof': 0
                            })
                        
                    elif ptype == 'order_update':
                        d = payload['data']
                        oid = str(d['id'])
                        if self.tree.exists(oid):
                            item = self.tree.item(oid)['values']
                            if item:
                                self.tree.item(oid, values=(item[0], item[1], item[2], item[3], d['res'], f"${d['prof']:.2f}"))
                            # Actualizar marcador del gráfico
                            for m in self.trade_markers:
                                if m['id'] == oid:
                                    m['result'] = d['res']
                                    m['prof'] = d.get('prof', 0)
                                    break
                            # Actualizar PnL
                            profit = d.get('prof', 0)
                            if d['res'] == 'WIN':
                                self.pnl_wins += 1
                            elif d['res'] == 'LOSS':
                                self.pnl_losses += 1
                            self.pnl_total += profit
                            total_ops = self.pnl_wins + self.pnl_losses
                            win_rate = (self.pnl_wins / total_ops * 100) if total_ops > 0 else 0
                            pnl_color = "#A6E3A1" if self.pnl_total >= 0 else "#F38BA8"
                            self.lbl_pnl.config(
                                text=f"W:{self.pnl_wins} | L:{self.pnl_losses} | {win_rate:.0f}% | P/L: ${self.pnl_total:.2f}",
                                foreground=pnl_color
                            )
                except Exception as e:
                    print(f"Error procesando mensaje de UI: {e}")

        except queue.Empty:
            pass
        
        # Repite cada 100ms
        self.root.after(100, self.process_queue)

    def _update_interpretation(self, sd):
        """Genera mensajes en lenguaje simple sobre qué analiza el bot."""
        score = sd['total']
        threshold = 0.20
        rsi = self._last_rsi
        auto_on = self.auto_var.get()

        # --- Estado principal ---
        if self._cooldown_remaining > 0 and auto_on:
            estado = f"⏳  Cooldown activo — próxima oportunidad en {self._cooldown_remaining}s"
            estado_color = "#F9E2AF"
        elif not auto_on:
            estado = "🔕  Auto-trading desactivado — solo manual"
            estado_color = "#6C7086"
        elif score >= threshold:
            estado = "✅  SEÑAL DE COMPRA (CALL ↑)"
            estado_color = "#A6E3A1"
        elif score <= -threshold:
            estado = "✅  SEÑAL DE VENTA (PUT ↓)"
            estado_color = "#F38BA8"
        elif score > 0:
            falta = threshold - score
            estado = f"🔍  Casi CALL — falta +{falta:.2f} de score"
            estado_color = "#F9E2AF"
        elif score < 0:
            falta = threshold + score
            estado = f"🔍  Casi PUT — falta -{falta:.2f} de score"
            estado_color = "#F9E2AF"
        else:
            estado = "⏸  Sin señal — mercado neutral"
            estado_color = "#6C7086"

        self.lbl_interp_estado.config(text=estado, fg=estado_color)

        # --- Barra de score ---
        self.canvas_score_bar.update_idletasks()
        bw = self.canvas_score_bar.winfo_width()
        if bw > 10:
            self.canvas_score_bar.delete("all")
            mid = bw // 2
            # Línea de umbral
            self.canvas_score_bar.create_line(mid - int(threshold * mid), 0, mid - int(threshold * mid), 10, fill="#F38BA8", width=1)
            self.canvas_score_bar.create_line(mid + int(threshold * mid), 0, mid + int(threshold * mid), 10, fill="#A6E3A1", width=1)
            # Indicador del score actual
            sx = mid + int(score * mid)
            sx = max(2, min(bw - 2, sx))
            bar_color = "#A6E3A1" if score > 0 else "#F38BA8"
            self.canvas_score_bar.create_rectangle(mid, 1, sx, 9, fill=bar_color, outline="")
            # Centro
            self.canvas_score_bar.create_line(mid, 0, mid, 10, fill="#6C7086", width=1)

        # --- Factor dominante ---
        factores = {
            "Micro-momentum precio": sd['micro_momentum'],
            "Indicadores técnicos": sd['tech'],
            "Momentum sentimiento": sd['mood_momentum'],
            "Divergencia precio/mood": sd['divergence'],
            "Sentimiento base": sd['mood_base'],
            "ROC (velocidad)": sd['roc'],
            "Contrarian crowd": sd['fade_crowd'],
        }
        dom_nombre, dom_val = max(factores.items(), key=lambda x: abs(x[1]))
        if abs(dom_val) < 0.01:
            factor_msg = "Todos los indicadores neutros"
            factor_color = "#6C7086"
        elif dom_val > 0:
            factor_msg = f"↑ Mayor impulso: {dom_nombre} (+{dom_val:.2f})"
            factor_color = "#A6E3A1"
        else:
            factor_msg = f"↓ Mayor freno: {dom_nombre} ({dom_val:.2f})"
            factor_color = "#F38BA8"
        self.lbl_interp_factor.config(text=factor_msg, fg=factor_color)

        # --- Qué necesita para operar ---
        consejos = []
        if rsi < 30:
            consejos.append("RSI en sobreventa (bueno para CALL)")
        elif rsi > 70:
            consejos.append("RSI en sobrecompra (bueno para PUT)")
        else:
            dist_call = rsi - 30
            dist_put = 70 - rsi
            if dist_call < dist_put:
                consejos.append(f"RSI {rsi:.1f} — necesita bajar {dist_call:.1f}pts para sobreventa")
            else:
                consejos.append(f"RSI {rsi:.1f} — necesita subir {dist_put:.1f}pts para sobrecompra")

        if sd.get('coherence', 0):
            consejos.append("⚠ MicroMom y MoodMom contradictorios → señales atenuadas")

        self.lbl_interp_next.config(text=" · ".join(consejos) if consejos else "")

    def update_order_timers(self):
        """Actualiza el texto del Treeview con el tiempo restante para cada orden activa."""
        if self.is_closing: return
        
        try:
            to_delete = []
            for oid, exp_at in self.exp_tracker.items():
                if not self.tree.exists(oid):
                    to_delete.append(oid)
                    continue
                    
                rem = exp_at - time.time()
                if rem > 0:
                    mins = int(rem // 60)
                    secs = int(rem % 60)
                    time_str = f"Expira: {mins:02d}:{secs:02d}"
                    
                    item = self.tree.item(oid).get('values')
                    if not item or len(item) < 6: continue

                    # Solo actualizar si el resultado sigue siendo 'Esperando...' o similar
                    if "Esperando" in str(item[4]) or "Expira" in str(item[4]):
                        self.tree.item(oid, values=(item[0], item[1], item[2], item[3], time_str, item[5]))
                else:
                    to_delete.append(oid)
                    item = self.tree.item(oid).get('values')
                    if item and len(item) >= 6 and "Expira" in str(item[4]):
                        self.tree.item(oid, values=(item[0], item[1], item[2], item[3], "Cerrando...", item[5]))

            for oid in to_delete:
                if oid in self.exp_tracker:
                    del self.exp_tracker[oid]
        except Exception as e:
            print(f"Error en update_order_timers: {e}")
                
        self.root.after(1000, self.update_order_timers)

    def append_log(self, text):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def start_bot(self):
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)
        self.lbl_status.config(text="Estado: EJECUTANDO...", foreground="#A6E3A1")
        self.append_log("Iniciando hilo del bot...")
        
        self.bot = TradingBot(callback_update=self.bot_callback)
        # Sincronizar monto inicial
        try:
            self.bot.monto_operacion = float(self.sv_amount.get())
        except:
            self.bot.monto_operacion = MONTO_OPERACION
            
        self.bot_thread = threading.Thread(target=self.bot.run_trading_loop, daemon=True)
        self.bot_thread.start()

    def on_amount_change(self):
        if self.bot:
            try:
                val = float(self.sv_amount.get())
                self.bot.monto_operacion = val
            except:
                pass

    def stop_bot(self):
        if self.bot:
            self.bot.stop()
            self.append_log("Se envió señal de detener. Esperando fin del ciclo...")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)
        self.lbl_status.config(text="Estado: DETENIDO", foreground="#F38BA8")

    def on_auto_toggle(self):
        enabled = self.auto_var.get()
        if self.bot:
            self.bot.auto_trading = enabled
            if enabled:
                self.bot.auto_stopped = False  # Reset stop flag
                self.lbl_auto_timer.config(text="✅ Auto-trade listo para operar", foreground="#94E2D5")
        if enabled:
            self.append_log("AUTO-TRADING ACTIVADO. El bot operará según análisis y sentimiento.")
        else:
            self.append_log("AUTO-TRADING DESACTIVADO. Solo operaciones manuales.")
            self.lbl_auto_timer.config(text="")

    def on_asset_change(self, event):
        new_asset = self.cb_asset.get()
        self.ax.clear()
        self.ax.set_facecolor('#181825')
        self.canvas.draw()
        self.trade_markers = []  # Limpiar marcadores del activo anterior
        self.lf_metrics.config(text=f" Análisis en Vivo ({new_asset}) ")
        
        self.append_log(f"Comercio redirigido a: {new_asset}")
        if self.bot:
            # Cambio de activo asíncrono para no congelar la UI
            threading.Thread(target=self.bot.set_asset, args=(new_asset,), daemon=True).start()

    def on_closing(self):
        self.is_closing = True
        if self.bot:
            self.bot.stop()
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = BotGUI(root)
    root.mainloop()
