"""
Gestore delle posizioni su Interactive Brokers - TRADING AZIONARIO.
Sistema per trading di azioni su conto demo IBKR porta 7497.
"""

import os
from typing import Dict, Any, Optional
from ib_insync import IB, Stock, MarketOrder
import time
import nest_asyncio
from config.settings import TradingConfig

# Permette nested event loops
nest_asyncio.apply()


class PositionManager:
    """Gestisce le operazioni di trading azionario su Interactive Brokers Demo."""
    
    def __init__(self):
        """Inizializza il gestore posizioni per trading azionario."""
        self.ib = None
        self.host = os.getenv('IBKR_HOST', '127.0.0.1')
        self.port = int(os.getenv('IBKR_PORT', 7497))  # Porta demo
        self.client_id = int(os.getenv('IBKR_CLIENT_ID', 1))
        self.is_connected = False
        
        # Connessione a IBKR Demo
        self._connect()
        
    def _connect(self):
        """Connessione al conto demo IBKR per trading azionario."""
        try:
            print(f"Connessione IBKR Demo (Stock Trading): {self.host}:{self.port}")
            
            self.ib = IB()
            self.ib.connect(
                host=self.host, 
                port=self.port, 
                clientId=self.client_id,
                timeout=10
            )
            
            self.is_connected = True
            print(f"Connesso a IBKR Demo - Trading Azionario Attivo")
            
            # Info account demo
            accounts = self.ib.managedAccounts()
            print(f"Account Demo: {accounts[0] if accounts else 'N/A'}")
            
        except Exception as e:
            print(f"Errore connessione IBKR: {e}")
            print("Verificare:")
            print("   - TWS Paper Trading attivo")
            print("   - API abilitato su porta 7497")
            print("   - Login demo completato")
            self.is_connected = False
            self.ib = None
    
    def test_connection(self) -> Dict[str, Any]:
        """Verifica connessione al broker per trading azionario."""
        if not self.is_connected or not self.ib:
            return {
                'connected': False,
                'error': 'IBKR Demo non connesso',
                'status': 'OFFLINE'
            }
        
        try:
            accounts = self.ib.managedAccounts()
            return {
                'connected': True,
                'account_id': accounts[0] if accounts else 'DEMO',
                'server': f"{self.host}:{self.port}",
                'status': 'CONNECTED',
                'market': 'STOCK_MARKET'
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e),
                'status': 'ERROR'
            }
    
    def open_position(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Apre posizione azionaria su IBKR Demo."""
        if not self.is_connected or not self.ib:
            return {
                'success': False,
                'error': 'IBKR Demo non connesso',
                'ticker': signal.get('ticker', ''),
                'action': signal.get('action', 'HOLD')
            }
        
        try:
            ticker = signal.get('ticker', '')
            action = signal.get('action', 'HOLD')
            entry_price = signal.get('entry_price', 0)
            stop_loss = signal.get('stop_loss', 0)
            take_profit = signal.get('take_profit', 0)
            
            # Usa position size dal segnale o da config
            shares = signal.get('position_size', TradingConfig.BASE_POSITION_SIZE)
            
            # Applica limiti di sicurezza
            shares = max(TradingConfig.MIN_POSITION_SIZE, 
                        min(TradingConfig.MAX_POSITION_SIZE, shares))
            
            if action == 'HOLD':
                return {
                    'success': False,
                    'error': 'Segnale HOLD - nessuna operazione',
                    'ticker': ticker,
                    'action': action
                }
            
            print(f"\nAPERTURA POSIZIONE AZIONARIA")
            print(f"   {action} {ticker}")
            print(f"   Prezzo: ${entry_price:.2f}")
            print(f"   Stop Loss: ${stop_loss:.2f}")
            print(f"   Take Profit: ${take_profit:.2f}")
            
            # Crea contratto azionario
            contract = self._create_stock_contract(ticker)
            if not contract:
                return {
                    'success': False,
                    'error': f'Azione {ticker} non trovata',
                    'ticker': ticker,
                    'action': action
                }
            
            # Crea ordine market
            order = MarketOrder(action, shares)
            order.tif = "DAY"  # Valido per la giornata
            
            print(f"Invio ordine: {action} {shares} azioni {ticker}")
            
            # Invia ordine al mercato
            trade = self.ib.placeOrder(contract, order)
            
            # Attende esecuzione
            self._wait_for_execution(trade, timeout=15)
            
            status = trade.orderStatus.status
            print(f"Status ordine: {status}")
            
            if status in ['Filled', 'PartFilled']:
                # Ordine eseguito con successo
                fill_price = trade.orderStatus.avgFillPrice or entry_price
                total_value = shares * fill_price
                
                result = {
                    'success': True,
                    'order_id': trade.order.orderId,
                    'ticker': ticker,
                    'action': action,
                    'shares': shares,
                    'fill_price': fill_price,
                    'total_value': total_value,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'timestamp': time.time(),
                    'status': 'EXECUTED'
                }
                
                print(f"POSIZIONE AZIONARIA APERTA!")
                print(f"   Order ID: {trade.order.orderId}")
                print(f"   Prezzo esecuzione: ${fill_price:.2f}")
                print(f"   Azioni: {shares}")
                print(f"   Valore totale: ${total_value:.2f}")
                
                return result
            else:
                return {
                    'success': False,
                    'error': f'Ordine non eseguito: {status}',
                    'ticker': ticker,
                    'action': action,
                    'order_status': status
                }
                
        except Exception as e:
            print(f"Errore apertura posizione azionaria: {e}")
            return {
                'success': False,
                'error': str(e),
                'ticker': signal.get('ticker', ''),
                'action': signal.get('action', 'HOLD')
            }
    
    def _create_stock_contract(self, ticker: str) -> Optional[Stock]:
        """Crea contratto per azione specifica."""
        try:
            print(f"Creazione contratto azione: {ticker}")
            
            # Crea contratto stock standard USA
            contract = Stock(ticker, 'SMART', 'USD')
            
            # Qualifica il contratto con IBKR
            qualified_contracts = self.ib.qualifyContracts(contract)
            
            if not qualified_contracts:
                print(f"Azione {ticker} non trovata su IBKR")
                return None
            
            qualified_contract = qualified_contracts[0]
            print(f"Contratto qualificato: {qualified_contract.symbol}")
            print(f"   Exchange: {qualified_contract.exchange}")
            print(f"   Valuta: {qualified_contract.currency}")
            
            return qualified_contract
            
        except Exception as e:
            print(f"Errore creazione contratto {ticker}: {e}")
            return None
    
    def _wait_for_execution(self, trade, timeout: int = 15):
        """Attende esecuzione ordine azionario."""
        start_time = time.time()
        print(f"Attesa esecuzione ordine (max {timeout}s)...")
        
        while time.time() - start_time < timeout:
            self.ib.sleep(0.1)  # Check ogni 100ms
            
            status = trade.orderStatus.status
            if status in ['Filled', 'Cancelled', 'ApiCancelled', 'Inactive']:
                break
                
        elapsed = time.time() - start_time
        print(f"Attesa completata dopo {elapsed:.1f}s")
    
    def get_positions_summary(self) -> Dict[str, Any]:
        """Riassunto posizioni azionarie."""
        return {
            'connection_status': 'CONNECTED' if self.is_connected else 'OFFLINE',
            'trading_mode': 'STOCK_DEMO',
            'market_type': 'EQUITIES'
        }
    
    def disconnect(self):
        """Disconnette da IBKR."""
        try:
            if self.is_connected and self.ib:
                self.ib.disconnect()
                print("Disconnesso da IBKR Demo")
            self.is_connected = False
            self.ib = None
        except Exception as e:
            print(f"Errore disconnessione: {e}")
