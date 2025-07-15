"""
Probabilità (Pr): valuta la forza del segnale ricevuto da MT4 indipendentemente dalla strategia che lo ha generato.
"""

from typing import Dict, Any
import time

class ProbabilityAnalyzer:
    """
    Calcola l'indice di probabilità come:
    Pr = strategy_signal * confidence
    
    La strategia MT4 deve fornire:
    - direction: direzione del segnale
    - strategy_signal: segnale [0,1] basato sugli indicatori
    - confidence: confidenza [0,1] sulla concordanza degli indicatori
    """
    
    def calculate_probability(self, signal_data: Dict[str, Any]) -> float:
        """
        Calcola probabilità come prodotto di segnale e confidenza.
        
        Args:
            signal_data: Dict contenente:
                - direction: 'BUY', 'SELL' o 'HOLD' (obbligatorio)
                - strategy_signal: forza del segnale [0,1] (obbligatorio)
                - confidence: confidenza [0,1] (obbligatorio)
                
        Returns:
            Probabilità normalizzata [0,1]
        """
        required_fields = ['direction', 'strategy_signal', 'confidence']
        
        # Validazione campi
        if not all(field in signal_data for field in required_fields):
            print(f"Errore calcolo probabilità: Segnale deve contenere: {required_fields}")
            return 0.5  # valore neutro in caso di errore
            
        # Estrai valori
        strategy_signal = float(signal_data['strategy_signal'])
        confidence = float(signal_data['confidence'])
        
        # Calcola probabilità
        probability = strategy_signal * confidence
        
        return min(1.0, max(0.0, probability)) 