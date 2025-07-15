"""
Server Flask API per ricezione segnali da MetaTrader 4.
Espone endpoints REST per comunicazione diretta con strategia MQL4.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import time

from uncertainty.reliability import ReliabilityCalculator
from trading.position_manager import PositionManager
from trading.signal_processor import SignalProcessor
from config.settings import TradingConfig
from utils.technical_analysis import Signal

# Carica le variabili d'ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)

# Inizializza i componenti principali
position_manager = PositionManager()
signal_processor = SignalProcessor()

# Semplifichiamo app_state per tracciare solo segnali e posizioni
app_state = {
    'signals': [],  # Lista degli ultimi segnali ricevuti
    'positions': [], # Lista delle posizioni aperte
    'last_update': time.time(),
    'total_signals_received': 0,
    'positions_opened': 0,
    'positions_rejected': 0
}

def update_app_state(signal_data: dict, reliability_data: dict, position_result: dict):
    """
    Aggiorna app_state con nuovo segnale e risultato posizione
    """
    app_state['total_signals_received'] += 1
    
    # Crea entry per il segnale
    signal_entry = {
        'timestamp': time.time(),
        'ticker': signal_data['ticker'],
        'direction': signal_data['direction'],
        'entry_price': signal_data['entry_price'],
        'stop_loss': signal_data['stop_loss'],
        'take_profit': signal_data['take_profit'],
        'reliability_score': reliability_data['reliability'],
        'reliability_details': {
            'probability': reliability_data['probability'],
            'plausibility': reliability_data['plausibility'],
            'credibility': reliability_data['credibility'],
            'possibility': reliability_data['possibility']
        },
        'position_opened': position_result['success'],
        'position_details': position_result
    }
    
    # Aggiungi alla lista segnali (mantieni ultimi 1000)
    app_state['signals'].append(signal_entry)
    if len(app_state['signals']) > 1000:
        app_state['signals'] = app_state['signals'][-1000:]
    
    # Aggiorna contatori
    if position_result['success']:
        app_state['positions_opened'] += 1
        # Aggiorna lista posizioni attive
        position = {
            'ticker': signal_data['ticker'],
            'direction': signal_data['direction'],
            'entry_price': position_result.get('fill_price', signal_data['entry_price']),
            'stop_loss': signal_data['stop_loss'],
            'take_profit': signal_data['take_profit'],
            'shares': position_result.get('shares', 0),
            'order_id': position_result.get('order_id', ''),
            'open_time': time.time(),
            'reliability_score': reliability_data['reliability']
        }
        app_state['positions'].append(position)
    else:
        app_state['positions_rejected'] += 1
    
    app_state['last_update'] = time.time()

@app.route('/')
def index():
    """Dashboard principale di monitoraggio."""
    return jsonify({
        'message': 'Server Financial Computing in esecuzione',
        'status': 'active',
        'endpoints': ['/api/signal', '/api/state'],
        'last_update': app_state['last_update']
    })

@app.route('/api/signal', methods=['POST'])
def receive_signal():
    """Riceve e processa segnale MT4"""
    try:
        signal_data = request.get_json()
        
        # Validazione campi obbligatori
        required_fields = ['direction', 'ticker', 'entry_price', 'stop_loss', 'take_profit', 'confidence', 'strategy_signal']
        missing_fields = [field for field in required_fields if field not in signal_data]
        
        if missing_fields:
            return jsonify({
                'error': f'Campi mancanti: {missing_fields}',
                'required_fields': required_fields
            }), 400
        
        # Aggiunge timeframe se mancante (default per MT4)
        if 'timeframe' not in signal_data:
            signal_data['timeframe'] = '15m'
        
        print(f"\n--- SEGNALE RICEVUTO ---")
        print(f"Ticker: {signal_data['ticker']}")
        print(f"Direction: {signal_data['direction']}")
        print(f"Entry Price: {signal_data['entry_price']}")
        print(f"Confidence: {signal_data['confidence']}")
        print(f"Strategy Signal: {signal_data['strategy_signal']}")
        
        # Inizializza ReliabilityCalculator con signal_data
        reliability_calc = ReliabilityCalculator(signal_data)
        
        # Calcola reliability
        reliability_data = reliability_calc.calculate_reliability(signal_data)
        
        print(f"\n--- ANALISI RELIABILITY ---")
        print(f"Probability: {reliability_data['probability']:.3f}")
        print(f"Plausibility: {reliability_data['plausibility']:.3f}")
        print(f"Credibility: {reliability_data['credibility']:.3f}")
        print(f"Possibility: {reliability_data['possibility']:.3f}")
        print(f"Reliability Score: {reliability_data['reliability']:.3f}")
        print(f"Threshold: {TradingConfig.RELIABILITY_THRESHOLD}")
        
        # Inizializza risultato posizione
        position_result = {'success': False, 'error': 'Reliability troppo bassa'}
        
        # Se affidabile, processa il segnale e apri posizione
        if reliability_data['reliability'] >= TradingConfig.RELIABILITY_THRESHOLD:
            # Processa il segnale
            processed_signal = signal_processor.process_signal(signal_data, reliability_data)
            
            if not processed_signal.get('error', False):
                # Apri posizione
                position_result = position_manager.open_position(processed_signal)
                
                if position_result['success']:
                    print(f"\n--- POSIZIONE APERTA ---")
                    print(f"Order ID: {position_result['order_id']}")
                    print(f"Fill Price: {position_result['fill_price']}")
                    print(f"Shares: {position_result['shares']}")
                else:
                    print(f"\n--- POSIZIONE RIFIUTATA ---")
                    print(f"Errore: {position_result['error']}")
            else:
                position_result = {
                    'success': False,
                    'error': processed_signal['error_message']
                }
        
        # Aggiorna stato
        update_app_state(signal_data, reliability_data, position_result)
        
        # Risposta al client
        if position_result['success']:
            return jsonify({
                'success': True,
                'message': f"Posizione aperta con reliability {reliability_data['reliability']:.3f}",
                'reliability_score': reliability_data['reliability'],
                'position_details': position_result,
                'reliability_details': reliability_data
            })
        else:
            return jsonify({
                'success': False,
                'message': f"Segnale rifiutato: {position_result['error']}",
                'reliability_score': reliability_data['reliability'],
                'reliability_details': reliability_data,
                'threshold': TradingConfig.RELIABILITY_THRESHOLD
            })
        
    except Exception as e:
        print(f"Errore processing segnale: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/state')
def get_state():
    """Restituisce stato corrente del sistema"""
    return jsonify({
        'system_status': 'active',
        'total_signals_received': app_state['total_signals_received'],
        'positions_opened': app_state['positions_opened'],
        'positions_rejected': app_state['positions_rejected'],
        'active_positions': len(app_state['positions']),
        'last_signals': app_state['signals'][-10:] if app_state['signals'] else [],
        'active_positions_details': app_state['positions'],
        'last_update': app_state['last_update'],
        'configuration': {
            'reliability_threshold': TradingConfig.RELIABILITY_THRESHOLD,
            'weights': {
                'probability': TradingConfig.WEIGHT_PROBABILITY,
                'plausibility': TradingConfig.WEIGHT_PLAUSIBILITY,
                'credibility': TradingConfig.WEIGHT_CREDIBILITY,
                'possibility': TradingConfig.WEIGHT_POSSIBILITY
            }
        }
    })

if __name__ == '__main__':
    print("=== FINANCIAL COMPUTING SERVER ===")
    print(f"Reliability Threshold: {TradingConfig.RELIABILITY_THRESHOLD}")
    print(f"Weights - Pr:{TradingConfig.WEIGHT_PROBABILITY}, Pl:{TradingConfig.WEIGHT_PLAUSIBILITY}, Cr:{TradingConfig.WEIGHT_CREDIBILITY}, Po:{TradingConfig.WEIGHT_POSSIBILITY}")
    print(f"Server starting on {TradingConfig.FLASK_HOST}:{TradingConfig.FLASK_PORT}")
    
    app.run(
        host=TradingConfig.FLASK_HOST,
        port=TradingConfig.FLASK_PORT,
        debug=TradingConfig.FLASK_DEBUG
    ) 