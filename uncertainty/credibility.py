"""
Credibilità (Cr): calcolata tramite sentiment analysis su notizie finanziarie istituzionali.
"""

from typing import Dict, Any
from utils.finance_news import FinanceNews
from utils.nlp_sentiment import NLPSentiment

class CredibilityAnalyzer:
    """
    Calcola l'indice di credibilità basato sul sentiment delle notizie economiche.
    """
    
    def __init__(self):
        self.finance_news = FinanceNews()
        self.nlp_sentiment = NLPSentiment()
        
    def calculate_credibility(self, ticker: str) -> float:
        """
        Calcola l'indice di credibilità per il ticker azionario.
        
        Args:
            ticker: Simbolo del ticker azionario
            
        Returns:
            Valore di credibilità normalizzato [0,1]
        """
        try:
            # Ottiene notizie istituzionali
            news_data = self.finance_news.get_ticker_news(ticker, max_items=15)
            
            if not news_data:
                return 0.5  # Valore neutro se non ci sono notizie
            
            # Analizza sentiment
            sentiments = []
            for news in news_data:
                text = f"{news.get('headline', '')} {news.get('summary', '')}"
                if text.strip():
                    sentiment = self.nlp_sentiment.analyze_sentiment(text, ticker)
                    sentiments.append(sentiment)
            
            if not sentiments:
                return 0.5
                
            # Calcola sentiment medio
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            # Normalizzazione sentiment medio tra 0 e 1 assumendo che il sentiment sia tra -1 e 1
            normalized_sentiment = (avg_sentiment + 1) / 2
            return normalized_sentiment
                
        except Exception as e:
            print(f"Errore calcolo credibilità per {ticker}: {e}")
            return 0.5 