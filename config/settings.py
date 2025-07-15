"""
Configurazioni centrali del sistema trading azionario.
Gestisce variabili d'ambiente e validazione per trading azioni.
"""

import os
from typing import Dict, Any, List
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()


class TradingConfig:
    """Configurazione principale del sistema trading azionario."""
    
    # API Keys
    FINNHUB_API_KEY = os.getenv('FINNHUB_API_KEY', '')
    LLM_API_KEY = os.getenv('LLM_API_KEY', '')
    
    # LLM Configuration
    LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.deepseek.com')
    LLM_MODEL_NAME = os.getenv('LLM_MODEL_NAME', 'deepseek-chat')
    
    # IBKR Configuration per azioni
    IBKR_HOST = os.getenv('IBKR_HOST', '127.0.0.1')
    IBKR_PORT = int(os.getenv('IBKR_PORT', 7497))
    IBKR_CLIENT_ID = int(os.getenv('IBKR_CLIENT_ID', 1))
    
    # Uncertainty Weights
    WEIGHT_PROBABILITY = float(os.getenv('WEIGHT_PROBABILITY', 0.3))
    WEIGHT_PLAUSIBILITY = float(os.getenv('WEIGHT_PLAUSIBILITY', 0.25))
    WEIGHT_CREDIBILITY = float(os.getenv('WEIGHT_CREDIBILITY', 0.25))
    WEIGHT_POSSIBILITY = float(os.getenv('WEIGHT_POSSIBILITY', 0.2))
    
    RELIABILITY_THRESHOLD = float(os.getenv('RELIABILITY_THRESHOLD', 0.6))

    # Position Size Settings
    BASE_POSITION_SIZE = float(os.getenv('BASE_POSITION_SIZE', '100'))
    MAX_POSITION_SIZE = float(os.getenv('MAX_POSITION_SIZE', '500'))
    MIN_POSITION_SIZE = float(os.getenv('MIN_POSITION_SIZE', '10'))
    
    # System Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Flask Configuration
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'

def get_config() -> Dict[str, Any]:
    """Restituisce configurazione sistema trading azionario."""
    return {
        'api_keys': {
            'finnhub': TradingConfig.FINNHUB_API_KEY,
            'llm': TradingConfig.LLM_API_KEY
        },
        'llm': {
            'base_url': TradingConfig.LLM_BASE_URL,
            'model_name': TradingConfig.LLM_MODEL_NAME
        },
        'ibkr': {
            'host': TradingConfig.IBKR_HOST,
            'port': TradingConfig.IBKR_PORT,
            'client_id': TradingConfig.IBKR_CLIENT_ID
        },
        'weights': {
            'probability': TradingConfig.WEIGHT_PROBABILITY,
            'plausibility': TradingConfig.WEIGHT_PLAUSIBILITY,
            'credibility': TradingConfig.WEIGHT_CREDIBILITY,
            'possibility': TradingConfig.WEIGHT_POSSIBILITY
        },
        'trading': {
            'reliability_threshold': TradingConfig.RELIABILITY_THRESHOLD,
            'base_position_size': TradingConfig.BASE_POSITION_SIZE,
            'max_position_size': TradingConfig.MAX_POSITION_SIZE,
            'min_position_size': TradingConfig.MIN_POSITION_SIZE
        },
        'system': {
            'log_level': TradingConfig.LOG_LEVEL,
            'flask_host': TradingConfig.FLASK_HOST,
            'flask_port': TradingConfig.FLASK_PORT,
            'flask_debug': TradingConfig.FLASK_DEBUG
        }
    }


def validate_config() -> Dict[str, List[str]]:
    """Valida configurazione sistema trading azionario."""
    errors = []
    warnings = []
    
    # Valida API keys
    if not TradingConfig.FINNHUB_API_KEY:
        warnings.append("FINNHUB_API_KEY non configurata - notizie azioni limitate")
        
    if not TradingConfig.LLM_API_KEY:
        warnings.append("LLM_API_KEY non configurata - sentiment analysis disabilitato")
    
    # Valida pesi (devono sommare a 1)
    total_weight = (TradingConfig.WEIGHT_PROBABILITY + 
                   TradingConfig.WEIGHT_PLAUSIBILITY + 
                   TradingConfig.WEIGHT_CREDIBILITY + 
                   TradingConfig.WEIGHT_POSSIBILITY)
    
    if abs(total_weight - 1.0) > 0.01:
        errors.append(f"I pesi degli indici non sommano a 1.0 (attuale: {total_weight:.3f})")
    
    if TradingConfig.RELIABILITY_THRESHOLD < 0.0 or TradingConfig.RELIABILITY_THRESHOLD > 1.0:
        errors.append(f"RELIABILITY_THRESHOLD deve essere tra 0.0 e 1.0 (attuale: {TradingConfig.RELIABILITY_THRESHOLD})")
    
    if TradingConfig.RELIABILITY_THRESHOLD < 0.5:
        warnings.append(f"RELIABILITY_THRESHOLD bassa ({TradingConfig.RELIABILITY_THRESHOLD}) - rischio elevato")

    # Valida dimensioni posizione
    if TradingConfig.BASE_POSITION_SIZE <= 0:
        errors.append("BASE_POSITION_SIZE deve essere maggiore di 0")
    
    if TradingConfig.MAX_POSITION_SIZE <= 0:
        errors.append("MAX_POSITION_SIZE deve essere maggiore di 0")

    if TradingConfig.MIN_POSITION_SIZE <= 0:
        errors.append("MIN_POSITION_SIZE deve essere maggiore di 0")    
    
    # Valida porte IBKR
    if TradingConfig.IBKR_PORT < 1024 or TradingConfig.IBKR_PORT > 65535:
        errors.append("IBKR_PORT non valida (deve essere tra 1024-65535)")
    
    if TradingConfig.FLASK_PORT < 1024 or TradingConfig.FLASK_PORT > 65535:
        errors.append("FLASK_PORT non valida (deve essere tra 1024-65535)")
    
    return {
        'errors': errors,
        'warnings': warnings
    }


def print_config_summary():
    """Stampa riassunto configurazione trading azionario."""
    config = get_config()
    validation = validate_config()
    
    print("=== CONFIGURAZIONE SISTEMA TRADING AZIONARIO ===")
    print(f"API Finnhub: {'✓' if config['api_keys']['finnhub'] else '✗'}")
    print(f"API LLM: {'✓' if config['api_keys']['llm'] else '✗'}")
    print(f"IBKR Demo: {config['ibkr']['host']}:{config['ibkr']['port']}")
    print(f"Flask Server: {config['system']['flask_host']}:{config['system']['flask_port']}")
    print(f"Pesi Incertezza: Pr={config['weights']['probability']:.2f}, Pl={config['weights']['plausibility']:.2f}, Cr={config['weights']['credibility']:.2f}, Po={config['weights']['possibility']:.2f}")
    print(f"Soglia Affidabilità: {config['trading']['reliability_threshold']:.2f}")
    print(f"Dimensioni Posizione: Min={config['trading']['min_position_size']}, Base={config['trading']['base_position_size']}, Max={config['trading']['max_position_size']}")
    
    if validation['errors']:
        print("\nERRORI:")
        for error in validation['errors']:
            print(f"  - {error}")
    
    if validation['warnings']:
        print("\nWARNINGS:")
        for warning in validation['warnings']:
            print(f"  - {warning}")
    
    if not validation['errors'] and not validation['warnings']:
        print("\nConfigurazione sistema trading azionario OK") 