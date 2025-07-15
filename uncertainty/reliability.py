"""
Affidabilità (A): combina i quattro indici di incertezza con pesi configurabili.
A = w1*Pr + w2*Pl + w3*Cr + w4*Po
"""

from typing import Dict, Any
from config.settings import TradingConfig
from .probability import ProbabilityAnalyzer
from .plausibility import PlausibilityAnalyzer  
from .credibility import CredibilityAnalyzer
from .possibility import PossibilityAnalyzer

class ReliabilityCalculator:
    """
    Calcola l'affidabilità combinando:
    - Probabilità (Pr): forza del segnale dalla strategia
    - Plausibilità (Pl): conferma da pattern tecnici
    - Credibilità (Cr): sentiment da notizie finanziarie
    - Possibilità (Po): assenza eventi macro destabilizzanti
    """
    
    def __init__(self, signal_data: Dict[str, Any]):
        """Inizializza il calcolatore con i quattro analizzatori."""
        self.probability_analyzer = ProbabilityAnalyzer()
        self.plausibility_analyzer = PlausibilityAnalyzer(signal_timeframe=signal_data['timeframe'])
        self.credibility_analyzer = CredibilityAnalyzer()
        self.possibility_analyzer = PossibilityAnalyzer()
        
        # Carica i pesi da TradingConfig
        self.weights = {
            'probability': TradingConfig.WEIGHT_PROBABILITY,
            'plausibility': TradingConfig.WEIGHT_PLAUSIBILITY,
            'credibility': TradingConfig.WEIGHT_CREDIBILITY,
            'possibility': TradingConfig.WEIGHT_POSSIBILITY
        }
        
    def calculate_reliability(self, signal_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcola l'affidabilità combinando i quattro indici.
        
        Args:
            signal_data: Dict contenente:
                - direction: 'BUY', 'SELL' o 'HOLD'
                - strategy_signal: forza segnale [0,1]
                - confidence: confidenza strategia [0,1]
                - ticker: simbolo del ticker
                
        Returns:
            Dict con scores e affidabilità finale:
            {
                'probability': float,    # [0,1]
                'plausibility': float,   # [0,1]
                'credibility': float,    # [0,1]
                'possibility': float,    # [0,1]
                'reliability': float,    # [0,1]
                'weights': Dict[str, float]
            }
        """
        try:
            # Validazione input
            if 'ticker' not in signal_data:
                raise ValueError("signal_data deve contenere 'ticker'")
            
            ticker = signal_data['ticker']
            
            # Calcola i quattro indici
            probability = self.probability_analyzer.calculate_probability(signal_data)
            plausibility = self.plausibility_analyzer.calculate_plausibility(ticker, signal_data['direction'])
            credibility = self.credibility_analyzer.calculate_credibility(ticker)
            possibility = self.possibility_analyzer.calculate_possibility(ticker)
            
            # Calcola affidabilità come somma pesata
            reliability = (
                self.weights['probability'] * probability +
                self.weights['plausibility'] * plausibility +
                self.weights['credibility'] * credibility +
                self.weights['possibility'] * possibility
            )
            
            return {
                'probability': probability,
                'plausibility': plausibility,
                'credibility': credibility,
                'possibility': possibility,
                'reliability': reliability,
                'weights': self.weights
            }
            
        except Exception as e:
            print(f"Errore nel calcolo affidabilità: {e}")
            return {
                'probability': 0.5,
                'plausibility': 0.5,
                'credibility': 0.5,
                'possibility': 0.5,
                'reliability': 0.5,
                'weights': self.weights
            }