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
                 context_lookback: int = 20):  # candele totali per contesto
        """
        Args:
            interval: intervallo temporale ('1d', '1h', etc.)
            context_lookback: candele totali per contesto
        """
        self.interval = interval
        self.context_lookback = context_lookback

    def _get_market_data(self, ticker: str):
        """Recupera dati di mercato con supporto forex."""
        try:
            # Converte ticker forex per yfinance
            yahoo_ticker = self._convert_to_yahoo_format(ticker)
            
            period_map = {
                "1m": "5d", "5m": "60d", "15m": "60d", 
                "30m": "60d", "1h": "730d", "4h": "730d", "1d": "2y"
            }
            period = period_map.get(self.interval, "60d")
            
            print(f"Download dati per {ticker} → {yahoo_ticker}")
            df = yf.download(
                yahoo_ticker, 
                period=period, 
                interval=self.interval, 
                progress=False,
                auto_adjust=False
            )
            
            if df.empty:
                print(f"Nessun dato trovato per {ticker}")
                return None
            
            return df
            
        except Exception as e:
            print(f"Errore recupero dati {ticker}: {e}")
            return None

    def _convert_to_yahoo_format(self, ticker: str) -> str:
        """Converte ticker per formato Yahoo Finance."""
        # Mapping forex
        forex_mapping = {
            'GBPUSD': 'GBPUSD=X',
            'EURUSD': 'EURUSD=X', 
            'USDJPY': 'USDJPY=X',
            'USDCHF': 'USDCHF=X',
            'AUDUSD': 'AUDUSD=X',
            'USDCAD': 'USDCAD=X',
            'NZDUSD': 'NZDUSD=X'
        }
        
        return forex_mapping.get(ticker, ticker)

    def get_candles(self, ticker: str) -> Optional[Dict]:
        """
        Recupera le ultime N candele OHLCV per il ticker basate sull'intervallo specificato.

        Args:
            ticker: simbolo del ticker

        Returns:
            Dizionario con arrays OHLCV o None se errore
        """
        try:
            # Scarica dati usando il periodo minimo necessario per l'intervallo
            df = self._get_market_data(ticker)
            if df is None:
                return None

            # Prendi solo le ultime N candele necessarie per l'analisi
            df = df.tail(self.context_lookback)
            
            print(f"Recuperate {len(df)} candele {self.interval} per {ticker}")
            
            # Verifica che abbiamo abbastanza candele
            if len(df) < self.context_lookback:
                print(f"Warning: Recuperate solo {len(df)} candele delle {self.context_lookback} richieste")
                
            data = {
                'open': df['Open'].values,
                'high': df['High'].values,
                'low': df['Low'].values,
                'close': df['Close'].values,
                'volume': df['Volume'].values,
                'dates': df.index.values
            }

            arrays = ['open', 'high', 'low', 'close', 'volume']

            # Controlla che tutti abbiano stessa lunghezza
            lengths = [len(data[key]) for key in arrays]
            if len(set(lengths)) > 1:
                print(f"Array con lunghezze diverse: {dict(zip(arrays, lengths))}")
                return []

            import numpy as np
            for key in arrays:
                # Assicura che sia numpy array 1D float64
                data[key] = np.array(data[key], dtype=np.float64).flatten()
                # Rimuovi NaN e infiniti
                data[key] = np.nan_to_num(data[key], nan=0.0, posinf=0.0, neginf=0.0)

            # print(f"Validazione OK: {len(data['open'])} candele")
            # print(f"Array info: open={data['open'].shape} {data['open'].dtype}")

            return data

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
