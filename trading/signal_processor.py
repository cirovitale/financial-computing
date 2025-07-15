"""
Processore dei segnali di trading.
Integra i segnali da MT4 con i punteggi di affidabilità per decisioni finali.
"""

from typing import Dict, Any
import time
from config.settings import TradingConfig

class SignalProcessor:
    """
    Processa i segnali di trading integrando analisi di affidabilità.
    """
    
    def __init__(self):
        """Inizializza il processore di segnali."""
        self.reliability_threshold = TradingConfig.RELIABILITY_THRESHOLD
        
    def process_signal(self, mt4_signal: Dict[str, Any], reliability_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Processa un segnale MT4 con i dati di affidabilità.
        
        Args:
            mt4_signal: Dict contenente:
                - ticker: str
                - direction: 'BUY'|'SELL'|'HOLD'
                - strategy_signal: float [0,1]
                - confidence: float [0,1]
                - entry_price: float
                - stop_loss: float
                - take_profit: float
            reliability_data: Dict contenente:
                - probability: float [0,1]
                - plausibility: float [0,1]
                - credibility: float [0,1]
                - possibility: float [0,1]
                - reliability: float [0,1]
            
        Returns:
            Dict con decisione finale e metadati
        """
        try:
            # Validazione input
            required_mt4_fields = ['ticker', 'direction', 'entry_price', 'stop_loss', 'take_profit']
            if not all(k in mt4_signal for k in required_mt4_fields):
                raise ValueError(f"Segnale MT4 mancante di campi richiesti: {required_mt4_fields}")
            
            # Estrae dati base del segnale
            ticker = mt4_signal['ticker']
            direction = mt4_signal['direction']
            entry_price = mt4_signal['entry_price']
            stop_loss = mt4_signal['stop_loss']
            take_profit = mt4_signal['take_profit']
            
            # Affidabilità complessiva
            reliability_score = reliability_data.get('reliability', 0)
            
            # Se affidabilità sotto threshold, rifiuta il segnale
            if reliability_score < self.reliability_threshold:
                return self._create_error_signal(mt4_signal, "Affidabilità insufficiente")
            
            # Altrimenti processa il segnale originale
            processed_signal = {
                'timestamp': time.time(),
                'ticker': ticker,
                'action': direction,
                'entry_price': entry_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'position_size': TradingConfig.BASE_POSITION_SIZE,
                'reliability_score': reliability_score,
                'reliability_details': reliability_data
            }
            
            return processed_signal
            
        except Exception as e:
            print(f"Errore processamento segnale: {e}")
            return self._create_error_signal(mt4_signal, str(e))
    
    
    
    def _create_error_signal(self, mt4_signal: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """
        Crea un segnale di errore con dati minimi.
        """
        return {
            'timestamp': time.time(),
            'ticker': mt4_signal.get('ticker', ''),
            'action': 'NONE',
            'entry_price': 0,
            'stop_loss': 0,
            'take_profit': 0,
            'position_size': 0,
            'reliability_score': 0,
            'error': True,
            'error_message': error_message
        }
