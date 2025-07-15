"""
Plausibilità (Pl): valutata tramite pattern candlestick confermativi.
"""

from typing import List, Dict
from utils.technical_analysis import TechnicalAnalyzer, Signal, PatternType

class PlausibilityAnalyzer:
    """
    Calcola la plausibilità (Pl) in base alla presenza di pattern candlestick confermativi.
    """

    def __init__(self, lookback: int = 5, signal_timeframe: str = "15m"):
        """
        Args:
            lookback: numero di candele recenti da considerare
            signal_timeframe: timeframe del segnale originale
        """
        self.lookback = lookback
        
        # Mapping dei timeframe per analisi multiframe
        timeframe_mapping = {
            "1m": "5m",
            "5m": "15m", 
            "15m": "1h",
            "30m": "4h",
            "1h": "4h",
            "4h": "1d"
        }
        
        # Usa il timeframe di conferma in base al timeframe del segnale
        confirmation_tf = timeframe_mapping.get(signal_timeframe, signal_timeframe)
        
        self.analyzer = TechnicalAnalyzer(
            interval=confirmation_tf,
            context_lookback=lookback
        )
    def calculate_plausibility(self, ticker: str, signal: Signal) -> float:
        """
        Calcola la plausibilità normalizzata [0,1].

        Args:
            ticker: simbolo del ticker
            signal: segnale da confermare (BUY/SELL/HOLD)

        Returns:
            Plausibilità normalizzata [0,1]
        """
        try:
            # Rileva pattern usando TechnicalAnalyzer
            patterns = self.analyzer.detect_patterns(ticker)
            if not patterns:
                print(f"Nessun pattern rilevato per {ticker}")
                return 0.0

            # Considera solo gli ultimi N pattern
            recent_patterns = sorted(patterns, key=lambda x: x['position'])[-self.lookback:]
            
            # Log dei pattern trovati
            print(f"\nPattern rilevati per {ticker} (ultimi {self.lookback}):")
            for pattern in recent_patterns:
                pattern_str = self.analyzer.format_pattern(pattern)
                confirmatory = "✓" if self._is_confirmatory(pattern['type'], signal) else " "
                print(f"  {confirmatory} {pattern_str}")
            
            # Calcola score con pesi decrescenti
            score = 0.0
            for i, pattern in enumerate(recent_patterns):
                weight = 1.0 - (i / len(recent_patterns)) * 0.5  # da 1.0 a 0.5
                
                # Pattern confermativo nella direzione del segnale
                if self._is_confirmatory(pattern['type'], signal):
                    score += weight * pattern['strength']  # Usa la forza del pattern
                # Pattern neutro
                elif pattern['type'] == PatternType.NEUTRAL:
                    score += 0.5 * weight

            print(f"\nPlausibilità finale per {ticker}: {score:.3f}")
            return min(1.0, score)
            
        except Exception as e:
            print(f"Errore calcolo plausibilità: {e}")
            return 0.5

    def _is_confirmatory(self, pattern_type: PatternType, signal: Signal) -> bool:
        """Verifica se il pattern conferma il segnale."""
        if signal == Signal.BUY and pattern_type == PatternType.BULLISH:
            return True
        if signal == Signal.SELL and pattern_type == PatternType.BEARISH:
            return True
        return False