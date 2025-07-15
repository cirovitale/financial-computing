"""
Modulo per l'analisi del sentiment tramite modelli NLP.
Utilizza DeepSeek o modelli Llama per valutare la polarità delle notizie.
"""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from openai import OpenAI


class SentimentMarketEventResponse(BaseModel):
    """
    Schema per la risposta di sentiment per notizie di mercato
    """
    score: float = Field(ge=-1.0, le=1.0, description="Score sentiment da -1 a +1")

class RelevanceEconomicCalendarEventResponse(BaseModel):
    """
    Schema per la risposta di sentiment per eventi economici
    """
    score: float = Field(ge=0.0, le=1.0, description="Score di rilevanza da 0 a 1")


class NLPSentiment:
    """
    Analizzatore di sentiment che utilizza API LLM per valutare
    la polarità emotiva dei testi finanziari.
    """
    
    def __init__(self):
        """
        Inizializza l'analizzatore NLP.
        """
        self.api_key = os.getenv('LLM_API_KEY')
        self.base_url = os.getenv('LLM_BASE_URL', 'https://api.deepseek.com')
        self.model_name = os.getenv('LLM_MODEL_NAME', 'deepseek-chat')
        
        if not self.api_key:
            print("LLM_API_KEY non trovata nelle variabili d'ambiente")
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
    
    def analyze_sentiment(self, text: str, ticker: str = None) -> float:
        """
        Analizza il sentiment di un testo.
        
        Args:
            text: Testo da analizzare
            ticker: Simbolo del titolo finanziario da analizzare
            
        Returns:
            Score sentiment da -1 (molto negativo) a +1 (molto positivo)
        """
        if not self.api_key or not text.strip():
            return 0.0
        
        try:
            # Prompt ottimizzato per analisi sentiment finanziario
            prompt = self._create_sentiment_prompt(text, ticker)
            
            # Chiamata all'API LLM
            response = self._call_llm_sentiment_api(prompt)
            
            if response:
                print(f"Risposta sentiment: {response}")
                return float(response)
            
            return 0.0
            
        except Exception as e:
            print(f"Errore nell'analisi sentiment: {e}")
            return 0.0
    
    def _create_sentiment_prompt(self, text: str, ticker: str = None) -> str:
        """
        Crea il prompt per l'analisi sentiment.
        
        Args:
            text: Testo da analizzare
            ticker: Simbolo del titolo finanziario
            
        Returns:
            Prompt formattato
        """
        ticker_context = f"rispetto al titolo {ticker}" if ticker else ""
        
        prompt = f"""
            Analizza il sentiment {ticker_context} del seguente testo di notizia finanziaria e restituisci SOLO un numero da -1 a +1:

            -1 = Molto negativo (bearish, crolli, crisi, vendite massicce)
            -0.5 = Negativo (preoccupazioni, cali, incertezza)
            0 = Neutro (informativo, senza bias emotivo)
            +0.5 = Positivo (ottimismo, crescita, opportunità)
            +1 = Molto positivo (bullish, rally, boom, acquisti massicci)

            Testo da analizzare:
            "{text}"

            Risposta (solo numero), da -1 a +1:
            """
        
        return prompt
    
    def _call_llm_sentiment_api(self, prompt: str) -> Optional[str]:
        """
        Effettua chiamata all'API del modello LLM.
        
        Args:
            prompt: Prompt da inviare
            response_format: Schema per la risposta del modello
        Returns:
            Risposta del modello o None se errore
        """
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Sei un analista finanziario esperto. Pensa step by step e restituisci la valutazione. Rispondi solo con un numero da -1 a +1."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.5,
                # response_format=SentimentMarketEventResponse
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Errore chiamata LLM API: {e}")
            return None
        
    def _call_llm_relevance_api(self, prompt: str) -> Optional[str]:
        """
        Effettua chiamata all'API del modello LLM.
        
        Args:
            prompt: Prompt da inviare
            response_format: Schema per la risposta del modello
        Returns:
            Risposta del modello o None se errore
        """
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Sei un analista finanziario esperto. Pensa step by step e restituisci la valutazione. Rispondi solo con un numero da 0 a 1."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.5,
                # response_format=RelevanceEconomicCalendarEventResponse
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Errore chiamata LLM API: {e}")
            return None

    def analyze_event_relevance(self, event_text: str, ticker: str, company_context: str) -> float:
        """
        Analizza quanto un evento economico è rilevante per un ticker.
        
        Args:
            event_text: Testo dell'evento da analizzare
            ticker: Simbolo del titolo
            company_context: Informazioni contestuali sull'azienda
            
        Returns:
            Score di rilevanza da 0 a 1
        """
        if not self.api_key or not event_text.strip():
            return 0.0
            
        try:
            prompt = f"""
            Analizza quanto il seguente evento economico è rilevante per il titolo {ticker}.
            
            Contesto Azienda:
            {company_context}
            
            Evento Economico:
            "{event_text}"
            
            Restituisci SOLO un numero da 0 a 1 che rappresenta la rilevanza:
            0 = Nessuna rilevanza (evento non correlato all'azienda o al suo settore)
            0.3 = Bassa rilevanza (impatto indiretto sul settore)
            0.6 = Media rilevanza (impatto diretto sul settore o indiretto sull'azienda)
            1.0 = Alta rilevanza (impatto diretto sull'azienda)
            
            Pensa step by step:
            1. L'evento riguarda direttamente l'azienda?
            2. L'evento impatta il settore dell'azienda?
            3. L'evento ha effetti sul mercato in cui opera l'azienda?
            4. Ci sono correlazioni tra l'evento e il business model dell'azienda?
            
            Risposta (solo numero), da 0 a 1:
            """
            
            response = self._call_llm_relevance_api(prompt)
            print(f"Risposta rilevanza evento: {response}")
            return float(response) if response else 0.0
            
        except Exception as e:
            print(f"Errore analisi rilevanza evento: {e}")
            return 0.0