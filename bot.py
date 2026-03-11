import os
import csv
from datetime import datetime
import json
import iqoptionapi.constants as OP_code
import time
import math
import logging
import threading
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option
from iqoptionapi.expiration import get_expiration_time

# Configuración básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ==========================================
# CONFIGURACIÓN DEL BOT
# ==========================================
ACTIVO = "BTCUSD"
TIEMPO_VELAS = 60         # 1 minuto
CANTIDAD_VELAS = 14       # Cantidad de periodos para calcular el RSI
MONTO_OPERACION = 1       # Inversión de $1 (USD/Minimo)
EXPIRACION = 1            # 1 Minuto de expiración
RSI_SOBRECOMPRA = 70
RSI_SOBREVENTA = 30
PERIODO_EMA = 20
PERIODO_SMA = 50
PERIODO_BOLLINGER = 20
DESVIACION_BOLLINGER = 2.0

# Funciones de cálculo matemático
def calcular_rsi(precios, periodos=14):
    if len(precios) < periodos + 1: return 50
    delta = [precios[i] - precios[i-1] for i in range(1, len(precios))]
    ganancias = [d if d > 0 else 0 for d in delta]
    perdidas = [-d if d < 0 else 0 for d in delta]
    avg_ganancia = sum(ganancias[:periodos]) / periodos
    avg_perdida = sum(perdidas[:periodos]) / periodos
    for i in range(periodos, len(delta)):
        avg_ganancia = (avg_ganancia * (periodos - 1) + ganancias[i]) / periodos
        avg_perdida = (avg_perdida * (periodos - 1) + perdidas[i]) / periodos
    if avg_perdida == 0: return 100
    rs = avg_ganancia / avg_perdida
    return 100 - (100 / (1 + rs))

def calcular_sma(precios, periodos):
    if len(precios) < periodos:
        return sum(precios) / len(precios) if len(precios) > 0 else 0
    return sum(precios[-periodos:]) / periodos

def calcular_ema(precios, periodos):
    if len(precios) < periodos:
        return calcular_sma(precios, len(precios))
    k = 2 / (periodos + 1)
    ema = calcular_sma(precios[:periodos], periodos)
    for precio in precios[periodos:]:
        ema = (precio - ema) * k + ema
    return ema

def calcular_bollinger(precios, periodos=20, desviaciones=2.0):
    if len(precios) < periodos: return 0, 0, 0
    sma = calcular_sma(precios, periodos)
    varianza = sum((x - sma)**2 for x in precios[-periodos:]) / periodos
    std_dev = math.sqrt(varianza)
    return sma + (std_dev * desviaciones), sma, sma - (std_dev * desviaciones)

class TradingBot:
    def __init__(self, callback_update=None):
        self.callback_update = callback_update
        self.running = False
        self.api = None
        self.interval = 6
        self.forced_trade_direction = None
        self.current_asset = ACTIVO
        self.monto_operacion = MONTO_OPERACION
        self.last_trade_time = 0
        self.auto_trading = False
        
        # === MARTINGALA ===
        self.martingala_enabled = True
        self.martingala_max_steps = 4       # Máximo 4 duplicaciones consecutivas
        self.martingala_current_step = 0    # Paso actual (0 = monto base)
        self.consecutive_losses = 0
        
        # === STOP-LOSS / TAKE-PROFIT ===
        self.stop_loss_pct = 10.0           # Detener si pierde 10% del balance inicial
        self.take_profit_pct = 15.0         # Detener si gana 15% del balance inicial
        self.initial_balance = None         # Se setea al conectar
        self.auto_stopped = False           # Flag: detenido por SL/TP
        
        # === FILTRO DE VOLATILIDAD ===
        self.volatility_filter = True
        self.min_bb_width_pct = 0.02
        
        # === TIMING DE ENTRADA ===  
        self.entry_timing_filter = True
        self.max_entry_second = 30
        
        # === HISTORIAL PARA ANTICIPACIÓN ===
        self.mood_history = []       # Últimos N valores de mood_call
        self.price_history = []      # Últimos N precios de cierre (5s candles)
        self.mood_history_max = 10   # Guardar últimos 10 análisis
        self.price_history_max = 30  # Últimos 30 precios (5s)
        
        # === HISTORIAL CSV ===
        self.csv_file = os.path.join(os.path.dirname(__file__), 'trade_history.csv')
        self._init_csv()
        
        # === LOG DE ANÁLISIS DETALLADO ===
        self.analysis_log = os.path.join(os.path.dirname(__file__), 'analysis_log.txt')
    
    def _log_analysis(self, asset, precio, rsi, ema, sma, bb_sup, bb_inf, mood, direccion, filtros_info="", score_details=None):
        """Guarda un registro detallado de cada análisis para mejora de estrategia."""
        try:
            bb_width = bb_sup - bb_inf
            bb_width_pct = (bb_width / precio) * 100 if precio > 0 else 0
            mood_put = 1.0 - mood
            
            scores_str = ""
            if score_details:
                scores_str = (
                    f"Score={score_details['total']:.3f} | "
                    f"MoodMom={score_details['mood_momentum']:.3f} | "
                    f"MicroMom={score_details['micro_momentum']:.3f} | "
                    f"Diverg={score_details['divergence']:.3f} | "
                    f"MoodBase={score_details['mood_base']:.3f} | "
                    f"Tech={score_details['tech']:.3f} | "
                    f"ROC={score_details['roc']:.3f} | "
                    f"FadeCrowd={score_details['fade_crowd']:.3f} | "
                )
            
            with open(self.analysis_log, 'a', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                        f"Asset={asset} | Precio={precio:.5f} | "
                        f"RSI={rsi:.2f} | EMA={ema:.5f} | SMA={sma:.5f} | "
                        f"BB_W%={bb_width_pct:.4f} | "
                        f"Mood_CALL={mood:.0%} | Mood_PUT={mood_put:.0%} | "
                        f"{scores_str}"
                        f"Decision={direccion or 'HOLD'} | {filtros_info}\n")
        except:
            pass
    
    # ========== ESTRATEGIAS DE ANTICIPACIÓN ==========
    # Cada método retorna un score entre -1.0 (PUT fuerte) y +1.0 (CALL fuerte)
    
    def _update_history(self, mood_call, precio, vela_chart):
        """Actualiza los historiales de mood y precio para las estrategias."""
        self.mood_history.append(mood_call)
        if len(self.mood_history) > self.mood_history_max:
            self.mood_history = self.mood_history[-self.mood_history_max:]
        
        # Agregar últimos precios de cierre de velas 5s
        if vela_chart:
            for v in vela_chart[-5:]:  # Últimas 5 velas nuevas
                self.price_history.append(v['close'])
            if len(self.price_history) > self.price_history_max:
                self.price_history = self.price_history[-self.price_history_max:]
    
    def _strategy_mood_momentum(self):
        """S1: Tendencia del sentimiento - ¿el mood está acelerando o frenando?"""
        if len(self.mood_history) < 4:
            return 0.0
        
        recent = self.mood_history[-4:]  # Últimos 4 análisis
        # Calcular deltas consecutivos
        deltas = [recent[i+1] - recent[i] for i in range(len(recent)-1)]
        avg_delta = sum(deltas) / len(deltas)
        
        # Si el mood CALL sube consistentemente → score positivo (CALL)
        # Si baja consistentemente → score negativo (PUT) 
        # Normalizar: delta de 0.05 por tick = señal fuerte
        score = max(-1.0, min(1.0, avg_delta * 20))
        return score
    
    def _strategy_fade_crowd(self, mood_call):
        """S2: Contrarian - Operar contra el sentimiento extremo (>85%)."""
        mood_put = 1.0 - mood_call
        
        if mood_call >= 0.85:
            # Demasiados compran → probablemente baje → PUT
            intensity = (mood_call - 0.85) / 0.15  # 0 a 1
            return -0.5 - (intensity * 0.5)  # -0.5 a -1.0
        elif mood_put >= 0.85:
            # Demasiados venden → probablemente suba → CALL
            intensity = (mood_put - 0.85) / 0.15
            return 0.5 + (intensity * 0.5)  # 0.5 a 1.0
        
        return 0.0  # No hay extremo
    
    def _strategy_divergence(self, mood_call):
        """S3: Divergencia precio/sentimiento - detecta reversiones inminentes."""
        if len(self.price_history) < 10 or len(self.mood_history) < 4:
            return 0.0
        
        # Tendencia de precio (últimos 10 precios)
        prices_recent = self.price_history[-10:]
        price_trend = (prices_recent[-1] - prices_recent[0]) / prices_recent[0] if prices_recent[0] > 0 else 0
        
        # Tendencia de mood (últimos 4 análisis)
        mood_trend = self.mood_history[-1] - self.mood_history[-4]
        
        # Divergencia: precio sube pero mood baja (o viceversa)
        if price_trend > 0.0005 and mood_trend < -0.05:
            # Precio sube, mood baja → reversión a la baja probable
            return -0.7
        elif price_trend < -0.0005 and mood_trend > 0.05:
            # Precio baja, mood sube → reversión al alza probable
            return 0.7
        
        return 0.0
    
    def _strategy_micro_momentum(self):
        """S4: Micro-momentum de precio (últimas 10 velas de 5s)."""
        if len(self.price_history) < 10:
            return 0.0
        
        recent = self.price_history[-10:]
        ups = 0
        downs = 0
        for i in range(1, len(recent)):
            if recent[i] > recent[i-1]:
                ups += 1
            elif recent[i] < recent[i-1]:
                downs += 1
        
        total = ups + downs
        if total == 0:
            return 0.0
        
        # Si 7+ de 9 movimientos son alcistas → momentum fuerte
        ratio = (ups - downs) / total  # -1 a +1
        return max(-1.0, min(1.0, ratio * 1.2))  # Amplificar ligeramente
    
    def _strategy_roc(self):
        """S5: Rate of Change - velocidad del movimiento del precio."""
        if len(self.price_history) < 15:
            return 0.0
        
        # ROC de los últimos 10 precios vs 5 antes de esos
        price_now = sum(self.price_history[-5:]) / 5
        price_before = sum(self.price_history[-15:-10]) / 5
        
        if price_before == 0:
            return 0.0
        
        roc = (price_now - price_before) / price_before
        
        # ROC positivo y fuerte → CALL, negativo → PUT
        # Normalizar: ROC de 0.001 (0.1%) = señal moderada
        score = max(-1.0, min(1.0, roc * 500))
        return score
    
    def _calculate_weighted_score(self, mood_call, rsi, ema, sma, bb_sup, bb_inf, precio):
        """Calcula score ponderado combinando las 5 estrategias + indicadores técnicos.
        v3: FadeCrowd x3 (15%), Diverg x1.2 (18%), threshold 0.22.
        Backtest sesión 03-11: -$0.55 real → +$1.70 simulado con estos pesos.
        """
        # Scores individuales
        s1 = self._strategy_mood_momentum()
        s2 = self._strategy_fade_crowd(mood_call)
        s3 = self._strategy_divergence(mood_call)
        s4 = self._strategy_micro_momentum()
        s5 = self._strategy_roc()
        
        # === FILTRO DE COHERENCIA ===
        # Si MoodMom y MicroMom apuntan en direcciones opuestas, anular ambas señales
        # (Dato del log: contradicciones entre estas 2 siempre resultaron en LOSS)
        coherence_penalty = 0
        if (s1 > 0.3 and s4 < -0.3) or (s1 < -0.3 and s4 > 0.3):
            coherence_penalty = 1  # Flag para penalizar
            s1 = s1 * 0.3  # Reducir fuerza de MoodMom al 30%
            s4 = s4 * 0.3  # Reducir fuerza de MicroMom al 30%
        
        # Sentimiento base (transformar mood 0-1 a score -1 a +1)
        mood_score = (mood_call - 0.5) * 2
        
        # === FILTRO MOOD NEUTRAL ===
        # Mood 40-60% tiene solo 33% win rate → penalizar
        if 0.40 <= mood_call <= 0.60:
            mood_score = mood_score * 0.3  # Reducir impacto del mood neutro
        
        # Indicadores técnicos como score
        tech_score = 0.0
        if rsi >= RSI_SOBRECOMPRA: tech_score -= 0.5
        elif rsi <= RSI_SOBREVENTA: tech_score += 0.5
        if precio >= bb_sup: tech_score -= 0.3
        elif precio <= bb_inf: tech_score += 0.3
        if ema > sma: tech_score += 0.2
        elif ema < sma: tech_score -= 0.2
        
        # === RSI BONUS (dato del log: RSI < 43 + CALL = 86% win rate) ===
        if rsi < 43:
            tech_score += 0.4  # Bonus alcista fuerte
        elif rsi > 57:
            tech_score -= 0.4  # Bonus bajista fuerte
        
        tech_score = max(-1.0, min(1.0, tech_score))
        
        # Ponderación v3 (sesión 2026-03-11: FadeCrowd correcto 3x consecutivas ignorado,
        # Diverg fue el único factor que discriminó el WIN real del rebote extremo)
        weighted = (
            s4 * 0.22 +     # Micro-Momentum precio (22% ↓ antes 25%)
            tech_score * 0.20 + # Indicadores técnicos (20%)
            s1 * 0.15 +     # Mood Momentum (15%)
            s3 * 0.18 +     # Divergencia (18% ↑ antes 15% — key en WIN RSI<30)
            mood_score * 0.05 + # Sentimiento base (5% ↓ antes 10% — crudo, menos confiable)
            s5 * 0.05 +     # Rate of Change (5% ↓ antes 10%)
            s2 * 0.15       # Fade the Crowd (15% ↑ antes 5% — fue correcto 3x seguidas)
        )
        
        details = {
            'mood_momentum': s1, 'fade_crowd': s2, 'divergence': s3,
            'micro_momentum': s4, 'roc': s5, 'mood_base': mood_score,
            'tech': tech_score, 'total': weighted, 'coherence': coherence_penalty
        }
        
        return weighted, details
    
    def _init_csv(self):
        """Inicializa el archivo CSV si no existe."""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'asset', 'direction', 'amount', 'result', 'profit', 'balance', 'mood', 'rsi'])
    
    def _save_trade_csv(self, asset, direction, amount, result, profit, balance, mood, rsi):
        """Guarda un trade en el historial CSV."""
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    asset, direction, amount, result, f"{profit:.2f}", f"{balance:.2f}", f"{mood:.2f}", f"{rsi:.2f}"
                ])
        except Exception as e:
            self.info(f"Error guardando CSV: {e}")
    
    def _get_martingala_amount(self):
        """Calcula el monto basado en Martingala controlada."""
        if not self.martingala_enabled:
            return self.monto_operacion
        multiplier = 2 ** min(self.consecutive_losses, self.martingala_max_steps)
        amount = self.monto_operacion * multiplier
        return amount
    
    def _check_stop_limits(self):
        """Verifica si se alcanzó el stop-loss o take-profit."""
        if self.initial_balance is None or self.initial_balance == 0:
            return False
        try:
            current = self.api.get_balance()
            change_pct = ((current - self.initial_balance) / self.initial_balance) * 100
            
            if change_pct <= -self.stop_loss_pct:
                self.info(f"⛔ STOP-LOSS ALCANZADO ({change_pct:.1f}%). Auto-trading detenido.")
                self.auto_stopped = True
                self.auto_trading = False
                self._emit('auto_stopped', 'STOP-LOSS')
                return True
            elif change_pct >= self.take_profit_pct:
                self.info(f"🎯 TAKE-PROFIT ALCANZADO ({change_pct:.1f}%). Auto-trading detenido.")
                self.auto_stopped = True
                self.auto_trading = False
                self._emit('auto_stopped', 'TAKE-PROFIT')
                return True
        except:
            pass
        return False

    def set_asset(self, new_asset):
        """Permite cambiar el par de divisas al vuelo desde la UI."""
        if self.api and self.api.check_connect():
            try:
                self.api.stop_mood_stream(self.current_asset, "turbo-option")
                self.api.start_mood_stream(new_asset, "turbo-option")
            except:
                pass
        self.current_asset = new_asset
        self.info(f"Cambiado activo a analizar: {self.current_asset}")

    def _emit(self, event_type, data):
        """Envía notificaciones a la interfaz si existe."""
        if self.callback_update:
            self.callback_update({'type': event_type, 'data': data})
            
    def info(self, text):
        logging.info(text)
        self._emit('status', text)

    def stop(self):
        self.running = False
        self.info("Deteniendo el bot...")

    def _wait_for_result(self, order_id, is_digital=False, timeout=180, trade_ctx=None, exp_at=None):
        """Hilo independiente para monitorear el resultado de una orden."""
        self.info(f"Iniciando seguimiento de orden {order_id}...")
        start = time.time()

        def _process_result(beneficio, res_str):
            """Procesa resultado: martingala + CSV + UI update."""
            self._emit('order_update', {'id': order_id, 'res': res_str, 'prof': beneficio})
            balance = self.api.get_balance()
            self._emit('balance', balance)

            # Martingala: resetear en WIN, incrementar en LOSS
            if res_str == 'WIN' or res_str == 'TIE':
                self.consecutive_losses = 0
            elif res_str == 'LOSS':
                self.consecutive_losses += 1
                if self.consecutive_losses > self.martingala_max_steps:
                    self.info(f"⚠ Martingala: máximo de {self.martingala_max_steps} pasos alcanzado. Reseteando.")
                    self.consecutive_losses = 0

            # Guardar en CSV
            if trade_ctx:
                self._save_trade_csv(
                    trade_ctx['asset'], trade_ctx['dir'], trade_ctx['amount'],
                    res_str, beneficio, balance, trade_ctx.get('mood', 0), trade_ctx.get('rsi', 50)
                )

        def _try_position_history():
            """Fallback REST: busca el resultado en historial de posiciones."""
            try:
                for opt_type in ("binary-option", "turbo-option"):
                    try:
                        positions = self.api.get_position_history_v2(opt_type, 10)
                        if not positions:
                            continue
                        items = positions.get('positions') or positions.get('items') or []
                        for pos in items:
                            pos_id = pos.get('raw_event', {}).get('option_id') or pos.get('id')
                            if str(pos_id) == str(order_id):
                                win_raw = pos.get('win', '')
                                profit = float(pos.get('profit', 0) or 0)
                                if win_raw == 'equal' or profit == 0:
                                    beneficio = 0
                                    res_str = 'TIE'
                                elif win_raw in ('win',) or profit > 0:
                                    beneficio = profit
                                    res_str = 'WIN'
                                else:
                                    amount = float(pos.get('amount', 0) or 0)
                                    beneficio = -amount if amount else profit
                                    res_str = 'LOSS'
                                self.info(f"[history] Resultado de Orden {order_id}: {res_str} (${beneficio:.2f})")
                                return beneficio, res_str
                    except Exception:
                        pass
            except Exception:
                pass
            return None, None

        try:
            if is_digital:
                while time.time() - start < timeout:
                    try:
                        check, result = self.api.check_win_digital_v2(order_id)
                        if check:
                            beneficio = result
                            res_str = "WIN" if beneficio > 0 else "LOSS" if beneficio < 0 else "TIE"
                            self.info(f"Resultado de Orden {order_id}: {res_str} (${beneficio})")
                            _process_result(beneficio, res_str)
                            return
                    except Exception:
                        pass
                    time.sleep(1)
            else:
                history_checked_at = None  # timestamp of last history check
                while time.time() - start < timeout:
                    now = time.time()
                    # Primary: websocket event
                    try:
                        if self.api.api.socket_option_closed.get(order_id) is not None:
                            x = self.api.api.socket_option_closed[order_id]
                            win_status = x['msg']['win']
                            if win_status == 'equal':
                                beneficio = 0
                            elif win_status == 'loose':
                                beneficio = float(x['msg']['sum']) * -1
                            else:
                                beneficio = float(x['msg']['win_amount']) - float(x['msg']['sum'])
                            res_str = "WIN" if beneficio > 0 else "LOSS" if beneficio < 0 else "TIE"
                            self.info(f"Resultado de Orden {order_id}: {res_str} (${beneficio:.2f})")
                            _process_result(beneficio, res_str)
                            return
                    except Exception:
                        pass

                    # Fallback REST: start polling 8s after expiry, every 15s
                    if exp_at is not None and now >= exp_at + 8:
                        if history_checked_at is None or now - history_checked_at >= 15:
                            history_checked_at = now
                            beneficio, res_str = _try_position_history()
                            if res_str is not None:
                                _process_result(beneficio, res_str)
                                return

                    time.sleep(1)

                # Last-chance history check before reporting TIMEOUT
                beneficio, res_str = _try_position_history()
                if res_str is not None:
                    _process_result(beneficio, res_str)
                    return

            self.info(f"Timeout esperando resultado de orden {order_id}.")
            self._emit('order_update', {'id': order_id, 'res': 'TIMEOUT', 'prof': 0})
            self._emit('balance', self.api.get_balance())
        except Exception as e:
            self.info(f"Error en seguimiento de orden {order_id}: {e}")
            self._emit('order_update', {'id': order_id, 'res': 'ERROR', 'prof': 0})

    def run_trading_loop(self):
        load_dotenv()
        email = os.getenv("IQ_EMAIL")
        password = os.getenv("IQ_PASSWORD")

        if not email or not password or email == "tu_correo@ejemplo.com":
            self.info("Error: Credenciales inválidas en .env")
            return

        # Limpiar log al inicio de cada ejecución
        try:
            with open(self.analysis_log, 'w', encoding='utf-8') as f:
                f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] === NUEVA SESION INICIADA ===\n")
        except:
            pass

        self.info("Conectando a IQ Option...")
        self.api = IQ_Option(email, password)
        check, reason = self.api.connect()

        if not check:
            self.info(f"Error al conectar: {reason}")
            return

        self.info("Conexión exitosa. Cuenta: PRACTICE.")
        self.api.change_balance("PRACTICE")
        self.initial_balance = self.api.get_balance()
        self._emit('balance', self.initial_balance)
        self.info(f"Balance inicial: ${self.initial_balance:.2f}")
        
        # Obtener lista de activos abiertos reales
        self.info("Obteniendo lista de activos y parcheando IDs faltantes...")
        open_assets = []
        try:
            # 1) Parchear IDs faltantes y obtener activos abiertos desde init_v2
            init_v2_data = self.api.get_all_init_v2()
            if init_v2_data:
                for option in ["binary", "turbo"]:
                    if option in init_v2_data:
                        for actives_id in init_v2_data[option].get("actives", {}):
                            active_data = init_v2_data[option]["actives"][actives_id]
                            try:
                                name = str(active_data["name"]).split(".")[1]
                                OP_code.ACTIVES[name] = int(actives_id)
                                
                                # Si el activo está habilitado y no suspendido, es operable
                                is_enabled = active_data.get("enabled", False)
                                is_suspended = active_data.get("is_suspended", True)
                                
                                if is_enabled and not is_suspended:
                                    # Ya no bloqueamos -op porque BTC a veces se lista así
                                    if name not in open_assets:
                                        open_assets.append(name)
                            except:
                                pass
                                
            # Eliminadas Opciones Digitales y Turbo para listado limpio (solo binarias puras)
            open_assets.sort()
            if open_assets:
                self._emit('assets', open_assets)
        except Exception as e:
            self.info(f"Fallo al obtener activos: {e}. Usando fijos.")
        
        # 3) Obtener historial previo de la cuenta
        self.info("Recuperando historial de operaciones recientes...")
        try:
            now = int(time.time())
            # Traer 10 de turbo y 10 de binary
            for h_type in ["turbo-option", "binary-option"]:
                check_h, data_h = self.api.get_position_history_v2(h_type, 10, 0, now, 0)
                if check_h and "positions" in data_h:
                    for pos in data_h["positions"]:
                        res_str = "WIN" if pos.get("close_profit", 0) > 0 else "LOSS" if pos.get("close_profit", 0) < 0 else "TIE"
                        dir_str = "CALL" if pos.get("instrument_dir") == "call" else "PUT"
                        h_time = datetime.fromtimestamp(pos.get("close_at", 0)/1000).strftime('%H:%M:%S')
                        
                        self._emit('order', {
                            'id': pos.get("id"), 
                            'time': h_time, 
                            'dir': dir_str, 
                            'amount': pos.get("invest", 0), 
                            'res': res_str, 
                            'prof': pos.get("close_profit", 0)
                        })
        except Exception as e:
            self.info(f"Fallo al recuperar historial: {e}")
            
        self.running = True

        # Iniciar stream de mood inicial
        try:
            self.api.start_mood_stream(self.current_asset, "turbo-option")
        except:
            pass

        while self.running:
            try:
                self.info(f"Analizando mercado: {self.current_asset}")
                velas_brutas = self.api.get_candles(self.current_asset, TIEMPO_VELAS, CANTIDAD_VELAS + 20, time.time())
                
                if not velas_brutas:
                    self.info(f"API retornó datos vacíos para {self.current_asset}. ¿Mercado cerrado o activo inválido OTC?")
                    contador = int(max(1, self.interval))
                    while contador > 0 and self.running:
                        self._emit('countdown', contador)
                        time.sleep(1)
                        contador -= 1
                    continue
                    
                precios_cierre = [v['close'] for v in velas_brutas]
                precio_actual = precios_cierre[-1]
                
                rsi_actual = calcular_rsi(precios_cierre, periodos=CANTIDAD_VELAS)
                ema_actual = calcular_ema(precios_cierre, periodos=PERIODO_EMA)
                sma_actual = calcular_sma(precios_cierre, periodos=PERIODO_SMA)
                bb_sup, bb_med, bb_inf = calcular_bollinger(precios_cierre, periodos=PERIODO_BOLLINGER, desviaciones=DESVIACION_BOLLINGER)
                
                # Fetch Traders Mood (Porcentaje de opciones CALL/Sube)
                mood_call = 0.5
                try:
                    mood_raw = self.api.get_traders_mood(self.current_asset)
                    if mood_raw: mood_call = mood_raw
                except:
                    pass
                
                # Fetch velas de 5 segundos para el gráfico en tiempo real (como IQ Option)
                vela_chart = []
                try:
                    velas_5s = self.api.get_candles(self.current_asset, 5, 60, time.time())
                    if velas_5s:
                        vela_chart = velas_5s
                except:
                    pass
                
                # Actualizar historial para estrategias de anticipación
                self._update_history(mood_call, precio_actual, vela_chart)
                
                # Enviar métricas y bools de strikes a la UI
                self._emit('metrics', {
                    'precio': precio_actual, 'rsi': rsi_actual,
                    'ema': ema_actual, 'sma': sma_actual,
                    'bb_sup': bb_sup, 'bb_inf': bb_inf,
                    'vela_hist': vela_chart if vela_chart else (velas_brutas[-40:] if len(velas_brutas) >= 40 else velas_brutas),
                    'mood_call': mood_call,
                    # Condiciones de venta (put)
                    'cond_put_rsi': bool(rsi_actual >= RSI_SOBRECOMPRA),
                    'cond_put_bb': bool(precio_actual >= bb_sup),
                    'cond_put_tend': bool(ema_actual < sma_actual),
                    'cond_put_mood': bool(mood_call < 0.45),
                    # Condiciones de compra (call)
                    'cond_call_rsi': bool(rsi_actual <= RSI_SOBREVENTA),
                    'cond_call_bb': bool(precio_actual <= bb_inf),
                    'cond_call_tend': bool(ema_actual > sma_actual),
                    'cond_call_mood': bool(mood_call > 0.55)
                })
                
                direccion = None
                score_details = None
                
                # Siempre calcular scores para el log (incluso en cooldown)
                try:
                    _, score_details = self._calculate_weighted_score(
                        mood_call, rsi_actual, ema_actual, sma_actual, bb_sup, bb_inf, precio_actual
                    )
                    self._emit('score_details', score_details)
                except:
                    pass
                
                # Cooldown dinámico: 120s si hay racha de pérdidas, 60s normal
                current_cooldown_time = 120 if getattr(self, 'consecutive_losses', 0) >= 2 else 60
                
                cooldown_elapsed = time.time() - self.last_trade_time
                if cooldown_elapsed < current_cooldown_time:
                    self._emit('cooldown_remaining', int(current_cooldown_time - cooldown_elapsed))
                    pass
                else:

                    # Lógica de FORZAR MANUAL (siempre disponibles)
                    if self.forced_trade_direction == "put":
                        self.info(f"TESTEO MANUAL: Venta (PUT) Forzada desde UI.")
                        direccion = "put"
                        self.forced_trade_direction = None
                    elif self.forced_trade_direction == "call":
                        self.info(f"TESTEO MANUAL: Compra (CALL) Forzada desde UI.")
                        direccion = "call"
                        self.forced_trade_direction = None
                    elif self.auto_trading and not self.auto_stopped:
                        
                        # === CHECK STOP-LOSS / TAKE-PROFIT ===
                        if self._check_stop_limits():
                            pass
                        else:
                            # === FILTRO DE VOLATILIDAD ===
                            bb_width = bb_sup - bb_inf
                            bb_width_pct = (bb_width / precio_actual) * 100 if precio_actual > 0 else 0
                            
                            if self.volatility_filter and bb_width_pct < self.min_bb_width_pct:
                                pass
                            else:
                                # === FILTRO DE TIMING ===
                                current_second = datetime.now().second
                                if self.entry_timing_filter and current_second > self.max_entry_second:
                                    pass
                                else:
                                    # === SISTEMA DE SCORING PONDERADO ===
                                    if score_details:
                                        score = score_details['total']
                                        threshold = 0.22
                                        
                                        if score >= threshold:
                                            self.info(f"AUTO [{score:.2f}]: CALL ↑ | MoodMom={score_details['mood_momentum']:.2f} MicroMom={score_details['micro_momentum']:.2f} Div={score_details['divergence']:.2f}")
                                            direccion = "call"
                                        elif score <= -threshold:
                                            self.info(f"AUTO [{score:.2f}]: PUT ↓ | MoodMom={score_details['mood_momentum']:.2f} MicroMom={score_details['micro_momentum']:.2f} Div={score_details['divergence']:.2f}")
                                            direccion = "put"
    
                    # Registrar análisis detallado en log
                    filtros = []
                    if cooldown_elapsed < current_cooldown_time: filtros.append("COOLDOWN")
                    if self.auto_stopped: filtros.append("AUTO_STOPPED")
                    self._log_analysis(
                        self.current_asset, precio_actual, rsi_actual, ema_actual, sma_actual,
                        bb_sup, bb_inf, mood_call, direccion, 
                        f"Filtros=[{','.join(filtros) if filtros else 'NONE'}]",
                        score_details=score_details
                    )
    
                    if direccion is not None:
                        # === MARTINGALA: calcular monto ===
                        monto = self._get_martingala_amount()
                        self.info(f"EJECUTANDO: {direccion.upper()} por ${monto} en {self.current_asset} (Martingala paso {self.consecutive_losses})")
                        
                        try:
                            status, id_orden = self.api.buy(monto, self.current_asset, direccion, EXPIRACION)
                            is_digital = False
    
                            if not status and "suspend" in str(id_orden).lower():
                                self.info("Binarias suspendidas. Intentando Digital...")
                                status, id_orden = self.api.buy_digital_spot(self.current_asset, monto, direccion, EXPIRACION)
                                is_digital = True
    
                            if status:
                                server_time = self.api.get_server_timestamp()
                                exp_timestamp, _ = get_expiration_time(server_time, EXPIRACION)
                                
                                dir_label = f"CALL ↑ Sube{' (DIG)' if is_digital else ''}" if direccion == "call" else f"PUT ↓ Baja{' (DIG)' if is_digital else ''}"
                                self.info(f"Orden ingresada (ID: {id_orden}). Monitoreando...")
                                self._emit('order', {
                                    'id': id_orden, 
                                    'time': time.strftime('%H:%M:%S'), 
                                    'dir': dir_label, 
                                    'amount': monto, 
                                    'res': 'Esperando...', 
                                    'prof': 0,
                                    'exp_at': exp_timestamp
                                })
                                
                                # Guardar contexto para CSV
                                trade_ctx = {
                                    'asset': self.current_asset, 'dir': direccion,
                                    'amount': monto, 'mood': mood_call, 'rsi': rsi_actual
                                }
                                
                                threading.Thread(
                                    target=self._wait_for_result,
                                    args=(id_orden, is_digital),
                                    kwargs={'trade_ctx': trade_ctx, 'exp_at': exp_timestamp},
                                    daemon=True
                                ).start()
                                
                                self.last_trade_time = time.time()
                                self.info("Cooldown activado (60s). El análisis continúa...")
                            else:
                                self.info(f"IQ Option rechazó la orden: {id_orden}")
    
                        except Exception as e:
                            self.info(f"Fallo crítico en ejecución: {e}")
                
                # Actualizar balance al final de cada ciclo
                try:
                    self._emit('balance', self.api.get_balance())
                except:
                    pass

                # Pausa de ciclo dinámica
                contador = int(max(1, self.interval))
                while contador > 0 and self.running:
                    self._emit('countdown', contador)
                    time.sleep(1)
                    contador -= 1

            except Exception as e:
                self.info(f"Excepción: {e}")
                if self.api and not self.api.check_connect():
                    self.info("Conexión perdida. Intentando reconectar...")
                    self.api.connect()
                    time.sleep(2)
                time.sleep(10)

def main():
    bot = TradingBot()
    bot.run_trading_loop()

if __name__ == "__main__":
    main()
