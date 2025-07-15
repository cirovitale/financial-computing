"""
Modulo per il recupero di notizie aziendali tramite API Finnhub (usando finnhub-python).
Fornisce notizie specifiche per ticker azionari con filtraggio.
"""

import os
import finnhub
from typing import List, Dict, Any
from datetime import datetime, timedelta
from .nlp_sentiment import NLPSentiment
import investpy

class FinanceNews:
    """
    Classe per recuperare notizie aziendali da Finnhub API.
    Gestisce il recupero e filtraggio delle news per ticker azionari specifici.
    """

    def __init__(self):
        """Inizializza il client per le notizie aziendali usando finnhub-python."""
        self.api_key = os.getenv('FINNHUB_API_KEY')

        if not self.api_key:
            print("Warning: FINNHUB_API_KEY non trovata nelle variabili d'ambiente")
            self.finnhub_client = None
        else:
            self.finnhub_client = finnhub.Client(api_key=self.api_key)

    def get_ticker_news(self, ticker: str, max_items: int = 10) -> List[Dict[str, Any]]:
        """
        Recupera le notizie per un ticker azionario specifico.

        Args:
            ticker: Simbolo del ticker azionario (es. 'AAPL', 'MSFT')
            max_items: Numero massimo di notizie da recuperare

        Returns:
            Lista di notizie aziendali con metadata
        """
        if not self.api_key or not self.finnhub_client:
            print(f"API Key mancante per recupero notizie {ticker}")
            return []

        try:
            print(f"Recupero notizie per azione {ticker}...")

            # Ottiene info azienda per migliorare ricerca
            company_info = self._get_company_info(ticker)

            # Cerca notizie con diversi approcci
            all_news = []

            # 1. News specifiche per il ticker (max 15)
            company_news = self._fetch_company_news(ticker)
            all_news.extend(company_news[:max_items])

            # 2. News generali filtrate per rilevanza (max 15)
            general_news = self._fetch_general_market_news(ticker, company_info)
            all_news.extend(general_news[:max_items])

            print(f"Trovate {len(all_news)} notizie rilevanti per {ticker}")
            return all_news

        except Exception as e:
            print(f"Errore recupero notizie per {ticker}: {e}")
            return []

    def get_economic_calendar_news(self, ticker: str, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Recupera eventi dal calendario economico usando investpy e analizza rilevanza per il ticker.
        
        Args:
            ticker: Simbolo da analizzare
            start_date: Data inizio (YYYY-MM-DD)
            end_date: Data fine (YYYY-MM-DD)
        """
        try:
            # Ottieni info base del ticker
            company_info = self._get_company_info(ticker)
            
            # Recupera eventi
            events = self._fetch_economic_calendar(start_date, end_date)
            
            # Analizza rilevanza di ogni evento
            nlp = NLPSentiment()
            relevant_events = []
            
            for event in events:
                company_context = f"Company: {company_info['name']}, Industry: {company_info['industry']}, Sector: {company_info['industry']}"
                event_text = f"Event: {event.get('event')}, Importance: {event.get('importance')}, Country: {event.get('zone')}, Forecast: {event.get('forecast')}"
                
                # Analizza rilevanza evento per il ticker
                relevance = nlp.analyze_event_relevance(
                    event_text=event_text,
                    ticker=ticker,
                    company_context=company_context
                )
                print(f"Economic Calendar Event:\n")
                print(f"  └─ Economic Calendar Event: {event}")
                print(f"  └─ Company Context: {company_context}")
                print(f"  └─ Relevance: {relevance}")
                
                if relevance > 0.5:  # soglia minima rilevanza
                    event['relevance_score'] = relevance
                    relevant_events.append(event)
            
            # Ordina per rilevanza
            relevant_events.sort(key=lambda x: x['relevance_score'], reverse=True)
            print(f"Trovati {len(relevant_events)} eventi rilevanti per {ticker}")
            
            return relevant_events
            
        except Exception as e:
            print(f"Errore analisi eventi per {ticker}: {e}")
            return []
        
    def _fetch_economic_calendar(self, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """
        Recupera il calendario economico usando investpy.

        Args:
            start_date: Data inizio (formato 'YYYY-MM-DD'), default oggi
            end_date: Data fine (formato 'YYYY-MM-DD'), default oggi + 30 giorni

        Returns:
            Lista di eventi economici
        """
        try:
            

            today = datetime.now()
            if not start_date:
                start_date = today.strftime('%Y-%m-%d')
            if not end_date:
                end_date = (today + timedelta(days=3)).strftime('%Y-%m-%d')

            # Converti le date nel formato richiesto da investpy (dd/mm/yyyy)
            start_date_formatted = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            end_date_formatted = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')

            # Recupera il calendario economico
            calendar = investpy.news.economic_calendar(
                from_date=start_date_formatted,
                to_date=end_date_formatted,
                importances=['high', 'medium']
            )

            # Converti il DataFrame in lista di dizionari
            events = calendar.to_dict('records')

            # Standardizza i nomi dei campi per mantenere compatibilità
            standardized_events = []
            for event in events:
                standardized_event = {
                    'event': event.get('event', ''),
                    'country': event.get('zone', ''),
                    'importance': event.get('importance', ''),
                    'date': event.get('date', ''),
                    'forecast': event.get('forecast', ''),
                    'zone': event.get('zone', '')
                }
                standardized_events.append(standardized_event)

            return standardized_events

        except Exception as e:
            print(f"Errore nel recupero del calendario economico: {e}")
            return []

    def _get_company_info(self, ticker: str) -> Dict[str, Any]:
        """
        Recupera informazioni base dell'azienda per migliorare ricerca news.

        Args:
            ticker: Simbolo ticker azionario

        Returns:
            Dizionario con info azienda
        """
        try:
            if not self.finnhub_client:
                raise Exception("Finnhub client non inizializzato")
            company_data = self.finnhub_client.company_profile2(symbol=ticker)
            return {
                'name': company_data.get('name', ''),
                'industry': company_data.get('finnhubIndustry', ''),
                'market_cap': company_data.get('marketCapitalization', 0),
                'country': company_data.get('country', ''),
                'ticker': ticker
                
            }
        except Exception as e:
            print(f"Impossibile recuperare info azienda per {ticker}: {e}")
            return {'name': '', 'industry': '', 'industry': '', 'country': '', 'ticker': ticker, 'market_cap': 0}

    def _fetch_company_news(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Recupera notizie specifiche per l'azienda.

        Args:
            ticker: Simbolo ticker azionario

        Returns:
            Lista di notizie aziendali
        """
        try:
            if not self.finnhub_client:
                raise Exception("Finnhub client non inizializzato")
            # Calcola date range (ultimi 3 giorni per notizie aziendali)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3)
            from_date = start_date.strftime('%Y-%m-%d')
            to_date = end_date.strftime('%Y-%m-%d')
            
            # Aggiungi metadata per identificare fonte
            news_data = self.finnhub_client.company_news(ticker, _from=from_date, to=to_date)
            if isinstance(news_data, list):
                for item in news_data:
                    item['news_source'] = 'company_specific'
                    item['ticker_mentioned'] = ticker
            
            print(f"{len(news_data)} notizie recuperate per {ticker}")

            return news_data if isinstance(news_data, list) else []

        except Exception as e:
            print(f"Errore recupero company news per {ticker}: {e}")
            return []

    def _fetch_general_market_news(self, ticker: str, company_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Recupera notizie generali di mercato filtrate per rilevanza.

        Args:
            ticker: Simbolo ticker azionario
            company_info: Informazioni azienda

        Returns:
            Lista di notizie generali rilevanti
        """
        try:
            if not self.finnhub_client:
                raise Exception("Finnhub client non inizializzato")
            # Calcola date range (ultimi 3 giorni per news generali)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3)

            news_data = self.finnhub_client.general_news('general')

            # Filtra per data e rilevanza
            relevant_news = []
            
            for item in news_data:
                # Filtro per data
                news_time = item.get('datetime')
                if news_time:
                    news_dt = datetime.fromtimestamp(news_time)
                    if not (start_date <= news_dt <= end_date):
                        continue
                    
                if self._is_news_relevant_to_stock(item, ticker, company_info):
                    # Aggiungi metadata per identificare fonte
                    item['news_source'] = 'general_market'
                    item['ticker_mentioned'] = ticker
                    relevant_news.append(item)

            return relevant_news

        except Exception as e:
            print(f"Errore recupero general news per {ticker}: {e}")
            return []

    def _is_news_relevant_to_stock(self, news_item: Dict[str, Any], ticker: str, company_info: Dict[str, Any]) -> bool:
        """
        Verifica se una notizia generale è rilevante per il ticker azionario.

        Args:
            news_item: Dati della notizia
            ticker: Simbolo ticker
            company_info: Informazioni azienda

        Returns:
            True se la notizia è rilevante per il titolo
        """
        try:
            headline = news_item.get('headline', '').upper()
            summary = news_item.get('summary', '').upper()
            text = f"{headline} {summary}"

            # 1. Controllo diretto ticker
            if ticker.upper() in text:
                return True

            # 2. Controllo nome azienda
            company_name = company_info.get('name', '').upper()
            if company_name and len(company_name) > 3:
                # Cerca nome azienda (almeno prime 3 parole significative)
                name_words = [word for word in company_name.split() if len(word) > 3]
                for word in name_words[:3]:  # Prime 3 parole significative
                    if word in text:
                        return True

            return False

        except Exception:
            return False
