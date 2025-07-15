"""
Modulo per la gestione del trading.
Include processamento segnali e gestione posizioni su Interactive Brokers.
"""

from .signal_processor import SignalProcessor
from .position_manager import PositionManager

__all__ = [
    'SignalProcessor',
    'PositionManager'
] 