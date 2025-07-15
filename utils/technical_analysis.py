"""
Utility per analisi tecnica e pattern recognition.
Usa TA-Lib per pattern candlestick e yfinance per i dati di mercato.
"""

import talib
import numpy as np
import yfinance as yf
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from enum import Enum

class Signal(Enum):
    """Enum per i possibili segnali."""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class PatternType(Enum):
    """Enum per i tipi di pattern."""
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"
    NONE = "none"

class TechnicalAnalyzer:
    """Analizzatore tecnico per pattern candlestick."""
    
    # Pattern supportati con relativi pesi
    BULLISH_PATTERNS = {
        'CDLENGULFING': (talib.CDLENGULFING, 1.0),
        'CDLMORNINGSTAR': (talib.CDLMORNINGSTAR, 1.0),
        'CDLHAMMER': (talib.CDLHAMMER, 1.0),
        'CDLPIERCING': (talib.CDLPIERCING, 1.0),
        'CDLMARUBOZU': (talib.CDLMARUBOZU, 1.0)
    }
    
    BEARISH_PATTERNS = {
        'CDLENGULFING': (talib.CDLENGULFING, 1.0),
        'CDLEVENINGSTAR': (talib.CDLEVENINGSTAR, 1.0),
        'CDLSHOOTINGSTAR': (talib.CDLSHOOTINGSTAR, 1.0),
        'CDLDARKCLOUDCOVER': (talib.CDLDARKCLOUDCOVER, 1.0),
        'CDLMARUBOZU': (talib.CDLMARUBOZU, 1.0)
    }

    def __init__(self, 
                 interval: str = "15m",
                 context_lookback: int = 15):  # candele totali per contesto
        """
        Args:
            interval: intervallo temporale ('1d', '1h', etc.)
            context_lookback: candele totali per contesto
        """
        self.interval = interval
        self.context_lookback = context_lookback

    def get_candles(self, ticker: str) -> Optional[Dict]:
        """
        Recupera le ultime N candele OHLCV per il ticker basate sull'intervallo specificato.

        Args:
            ticker: simbolo del ticker

        Returns:
            Dizionario con arrays OHLCV o None se errore
        """
        try:
            # Mappa intervalli yfinance con periodi minimi necessari
            period_map = {
                '1m': '7d',     # yfinance limita 1m a 7 giorni
                '5m': '60d',    # yfinance limita 5m a 60 giorni
                '15m': '60d',   # yfinance limita 15m a 60 giorni
                '30m': '60d',   # yfinance limita 30m a 60 giorni
                '1h': '730d',   # yfinance limita 1h a 730 giorni
                '2h': '730d',   # yfinance limita 2h a 730 giorni
                '4h': '730d',   # yfinance limita 4h a 730 giorni
                '1d': 'max'     # nessun limite per dati giornalieri
            }

            if self.interval not in period_map:
                raise ValueError(f"Intervallo {self.interval} non supportato. Usa uno tra: {list(period_map.keys())}")

            # Scarica dati usando il periodo minimo necessario per l'intervallo
            stock = yf.Ticker(ticker)
            df = stock.history(
                period=period_map[self.interval],
                interval=self.interval
            )

            if df.empty:
                print(f"Nessun dato trovato per {ticker}")
                return None

            # Prendi solo le ultime N candele necessarie per l'analisi
            df = df.tail(self.context_lookback)
            
            print(f"Recuperate {len(df)} candele {self.interval} per {ticker}")
            
            # Verifica che abbiamo abbastanza candele
            if len(df) < self.context_lookback:
                print(f"Warning: Recuperate solo {len(df)} candele delle {self.context_lookback} richieste")
                
            return {
                'open': df['Open'].values,
                'high': df['High'].values,
                'low': df['Low'].values,
                'close': df['Close'].values,
                'volume': df['Volume'].values,
                'dates': df.index.values
            }

        except Exception as e:
            print(f"Errore recupero dati per {ticker}: {e}")
            return None

    def detect_patterns(self, ticker: str) -> List[Dict]:
        """
        Rileva pattern candlestick per un ticker.

        Args:
            ticker: simbolo del ticker

        Returns:
            Lista di pattern trovati con tipo e posizione
        """
        # Recupera dati
        data = self.get_candles(ticker)
        if not data:
            return []

        patterns = []
        
        # Pattern bullish
        for name, (func, weight) in self.BULLISH_PATTERNS.items():
            result = func(data['open'], data['high'], data['low'], data['close'])
            for i, value in enumerate(result):
                if value > 0:
                    patterns.append({
                        'name': name,
                        'type': PatternType.BULLISH,
                        'position': i,
                        'strength': weight,
                        'date': data['dates'][i]
                    })

        # Pattern bearish
        for name, (func, weight) in self.BEARISH_PATTERNS.items():
            result = func(data['open'], data['high'], data['low'], data['close'])
            for i, value in enumerate(result):
                if value < 0:
                    patterns.append({
                        'name': name,
                        'type': PatternType.BEARISH,
                        'position': i,
                        'strength': weight,
                        'date': data['dates'][i]
                    })

        # Pattern neutri (doji)
        for i in range(len(data['open'])):
            if self._is_doji(
                data['open'][i],
                data['high'][i],
                data['low'][i],
                data['close'][i]
            ):
                patterns.append({
                    'name': 'DOJI',
                    'type': PatternType.NEUTRAL,
                    'position': i,
                    'strength': 0.5,
                    'date': data['dates'][i]
                })

        return patterns

    def _is_doji(self, open: float, high: float, low: float, close: float) -> bool:
        """Verifica se una candela è un doji."""
        body = abs(close - open)
        return body <= 0.1 * (high - low)

    def format_pattern(self, pattern: Dict) -> str:
        """
        Formatta un pattern per il logging.
        
        Args:
            pattern: dizionario del pattern

        Returns:
            Stringa formattata del pattern
        """
        # Converti numpy.datetime64 in stringa YYYY-MM-DD
        date_str = str(pattern['date']).split('T')[0]
        
        return (f"{pattern['name']}: "
                f"{pattern['type'].value} "
                f"(strength={pattern['strength']:.2f}, "
                f"date={date_str})")
