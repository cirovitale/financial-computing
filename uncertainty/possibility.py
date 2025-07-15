"""
Possibilità (Po): valuta la stabilità del contesto in base agli eventi macroeconomici imminenti.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List
from utils.finance_news import FinanceNews

class PossibilityAnalyzer:
    """
    Calcola l'indice di possibilità basato sulla presenza/assenza 
    di eventi macroeconomici rilevanti nel calendario.
    """
    
    def __init__(self):
        """Inizializza l'analizzatore di possibilità."""
        self.finance_news = FinanceNews()
        
    def calculate_possibility(self, ticker: str) -> float:
        """
        Calcola l'indice di possibilità [0,1] basato su eventi economici.
        
        Args:
            ticker: Simbolo del ticker
            
        Returns:
            Possibilità normalizzata [0,1] dove:
            1.0 = nessun evento rilevante imminente
            0.0 = eventi ad alto impatto molto vicini
        """
        try:
            # Recupera eventi dei prossimi 5 giorni
            end_date = (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d')
            events = self.finance_news.get_economic_calendar_news(
                start_date=datetime.now().strftime('%Y-%m-%d'),
                end_date=end_date,
                ticker=ticker
            )

            if not events:
                return 1.0  # Nessun evento = massima possibilità

            # Calcola score per ogni evento
            scores = []
            for event in events:
                # Calcola giorni mancanti
                event_date = datetime.fromtimestamp(event.get('datetime', 0))
                days_until = (event_date - datetime.now()).total_seconds() / (24 * 3600)
                
                if days_until < 0:  # Evento passato
                    continue

                # Base score per temporalità
                if days_until > 3:
                    time_score = 1.0
                elif days_until > 2:
                    time_score = 0.8
                elif days_until > 1:
                    time_score = 0.6
                else:
                    time_score = 0.2

                # Modifica per importanza evento
                impact = event.get('impact', '').lower()
                if impact == 'high':
                    impact_multiplier = 0.5  # riduce score del 50%
                elif impact == 'medium':
                    impact_multiplier = 0.7  # riduce score del 30%
                elif impact == 'low':  # low
                    impact_multiplier = 0.9  # riduce score del 10%
                else:
                    impact_multiplier = 0.7

                final_score = time_score * impact_multiplier
                scores.append(final_score)

            if not scores:
                return 0.5

            # Il più basso score determina la possibilità
            possibility = min(scores)
            return max(0.0, min(1.0, possibility))

        except Exception as e:
            print(f"Errore calcolo possibilità: {e}")
            return 0.5 