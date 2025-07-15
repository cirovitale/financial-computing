//+------------------------------------------------------------------+
//|           Strategia Multi-Parametrica Vitale Ciro                |
//+------------------------------------------------------------------+

// === PARAMETRI CONFIGURABILI ===
extern double   LotSize               = 0.5;
extern int      EMA_Fast              = 13;
extern int      EMA_Slow              = 34;
extern int      RSI_Period            = 2;
extern double   RSI_Oversold          = 18.0;
extern int      BB_Period             = 20;
extern double   BB_Deviation          = 2.5;
extern int      Volume_MA_Period      = 20;
extern double   Volume_Multiplier     = 1.30;
extern double   RiskRewardRatio       = 3.0;
extern int      MaxOpenTrades         = 1;
extern int      NumParams = 4; 

// === PARAMETRI SERVER FLASK ===
extern string   FlaskServerURL        = "http://localhost/api/signal";
extern bool     SendSignalsToFlask    = true;   

int magicNumber = 123456;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit() {
   Print("===== Strategia Multi-Parametrica Vitale Ciro =====");
   Print("Flask Server URL: ", FlaskServerURL);
   Print("Invio segnali abilitato: ", SendSignalsToFlask);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick() {
   if(CountOpenTrades() >= MaxOpenTrades) return;

   bool trendSignal = CheckTrend();
   bool rsiSignal   = CheckRSI();
   bool bbSignal    = CheckBB();
   bool volSignal   = CheckVolume();

   int passCount = trendSignal + rsiSignal + bbSignal + volSignal;
   if(passCount < NumParams) return;   

   double sl = CalculateStopLoss();
   double tp = CalculateTakeProfit(sl);
   
   double confidence = CalculateDynamicConfidence(sl, tp);
   double strength   = CalculateStrength();

   if(SendSignalsToFlask) {
      SendOpenSignalToFlask("BUY", Ask, sl, tp, confidence, strength);
   }

   int ticket = OrderSend(Symbol(), OP_BUY, LotSize, Ask, 3, sl, tp, "StrategiaMultiVitaleCiro", magicNumber, 0, clrBlue);
   if(ticket < 0) {
      int err = GetLastError();

      Print("Errore ordine: ", err);

      if(SendSignalsToFlask) {
         SendErrorSignalToFlask("ERROR", err);
      }
   } else {
      Print("Ordine aperto con successo. Ticket: ", ticket);
   }

}

//+------------------------------------------------------------------+
//| Gestione eventi di trade (apertura/chiusura)                    |
//+------------------------------------------------------------------+
void OnTrade() {
   if(!SendSignalsToFlask) return;
   
   static int lastOrdersTotal = 0;
   int currentOrdersTotal = OrdersTotal();
   
   if(currentOrdersTotal < lastOrdersTotal) {
      // posizione chiusa
      SendCloseSignalToFlask();
   }
   lastOrdersTotal = currentOrdersTotal;
}

//+------------------------------------------------------------------+
//| Invio segnale di apertura al Flask server                       |
//+------------------------------------------------------------------+
void SendOpenSignalToFlask(string direction, double entryPrice, double stopLoss, double takeProfit, double confidence, double strength) {
   string jsonData = StringFormat(
      "{"
      "\"direction\":\"%s\","
      "\"ticker\":\"%s\","
      "\"entry_price\":%.5f,"
      "\"stop_loss\":%.5f,"
      "\"take_profit\":%.5f,"
      "\"confidence\":%.2f,"
      "\"strength\":%.2f,"
      "\"timeframe\":\"15m\","
      "\"timestamp\":\"%s\","
      "\"magic_number\":%d"
      "}",
      direction,
      Symbol(),
      entryPrice,
      stopLoss,
      takeProfit,
      confidence,
      strength,
      TimeToString(TimeCurrent()),
      magicNumber
   );
   
   SendHTTPRequest(jsonData);
}

//+------------------------------------------------------------------+
//| Invio segnale di chiusura al Flask server                       |
//+------------------------------------------------------------------+
void SendCloseSignalToFlask() {
   string jsonData = StringFormat(
      "{"
      "\"direction\":\"CLOSE\","
      "\"ticker\":\"%s\","
      "\"entry_price\":%.5f,"
      "\"stop_loss\":0.0,"
      "\"take_profit\":0.0,"
      "\"confidence\":%.2f,"
      "\"strength\":%.2f,"
      "\"timeframe\":\"15m\","
      "\"timestamp\":\"%s\","
      "\"magic_number\":%d"
      "}",
      Symbol(),
      Bid,
      0.0,
      0.0,
      TimeToString(TimeCurrent()),
      magicNumber
   );
   
   SendHTTPRequest(jsonData);
}

//+------------------------------------------------------------------+
//| Invio segnale di errore al Flask server                         |
//+------------------------------------------------------------------+
void SendErrorSignalToFlask(string errorType, int errorCode) {
   string jsonData = StringFormat(
      "{"
      "\"direction\":\"ERROR\","
      "\"ticker\":\"%s\","
      "\"entry_price\":%.5f,"
      "\"stop_loss\":0.0,"
      "\"take_profit\":0.0,"
      "\"confidence\":0.0,"
      "\"strength\":0.0,"
      "\"timeframe\":\"15m\","
      "\"timestamp\":\"%s\","
      "\"error_type\":\"%s\","
      "\"error_code\":%d,"
      "\"magic_number\":%d"
      "}",
      Symbol(),
      Bid,
      TimeToString(TimeCurrent()),
      errorType,
      errorCode,
      magicNumber
   );
   
   SendHTTPRequest(jsonData);
}

//+------------------------------------------------------------------+
//| Funzione per inviare richiesta HTTP al Flask server             |
//+------------------------------------------------------------------+
void SendHTTPRequest(string jsonData) {
   char postData[];
   string headers;
   char result[];
   string resultString;
   
   StringToCharArray(jsonData, postData, 0, StringLen(jsonData));
   
   headers = "Content-Type: application/json\r\n";
   
   Print("Invio dati al Flask server: ", jsonData);
   
   // Invia la richiesta HTTP POST
   int res = WebRequest(
      "POST",                    // Metodo
      FlaskServerURL,            // URL
      headers,                   // Headers
      600000,                     // Timeout
      postData,                  // Dati POST
      result,                    // Risultato
      resultString               // Risultato come stringa
   );
   
   if(res == -1) {
      int error = GetLastError();
      Print("Errore WebRequest: ", error);
      
      if(error == 4060) {
         Print("ERRORE: URL non consentito. Aggiungi ", FlaskServerURL, " alle impostazioni WebRequest di MT4");
      }
   } else {
      Print("Risposta Flask server (", res, "): ", resultString);
   }
}

//+------------------------------------------------------------------+
//| Conteggio posizioni aperte                                       |
//+------------------------------------------------------------------+
int CountOpenTrades() {
   int c = 0;
   for(int i=0; i<OrdersTotal(); i++) {
      if(OrderSelect(i, SELECT_BY_POS)
         && OrderMagicNumber() == magicNumber
         && OrderSymbol() == Symbol()) c++;
   }
   return(c);
}

//+------------------------------------------------------------------+
//| Controllo trend con EMA                                           |
//+------------------------------------------------------------------+
bool CheckTrend() {
   return(iMA(NULL,0,EMA_Fast,0,MODE_EMA,PRICE_CLOSE,0) > iMA(NULL,0,EMA_Slow,0,MODE_EMA,PRICE_CLOSE,0));
}

//+------------------------------------------------------------------+
//| Controllo RSI                                                   |
//+------------------------------------------------------------------+
bool CheckRSI() {
   double rsi = iRSI(NULL,0,RSI_Period,PRICE_CLOSE,0);
   return(rsi <= RSI_Oversold);
}

//+------------------------------------------------------------------+
//| Controllo Bollinger Bands                                        |
//+------------------------------------------------------------------+
bool CheckBB() {
   double mid = iBands(NULL,0,BB_Period,BB_Deviation,0,PRICE_CLOSE,MODE_MAIN,0);
   return(Close[0] > mid);
}

//+------------------------------------------------------------------+
//| Controllo volume semplice                                        |
//+------------------------------------------------------------------+
bool CheckVolume() {
   double vSum = 0;
   for(int i=1; i<=Volume_MA_Period; i++) vSum += Volume[i];
   double vMA = vSum / Volume_MA_Period;
   return(Volume[0] > vMA * Volume_Multiplier);
}

//+------------------------------------------------------------------+
//| Stop loss basato su ATR                                          |
//+------------------------------------------------------------------+
double CalculateStopLoss() {
   return(Ask - iATR(NULL,0,14,0) * 1.2);
}

//+------------------------------------------------------------------+
//| Take profit con R:R                                              |
//+------------------------------------------------------------------+
double CalculateTakeProfit(double stop) {
   double risk = Ask - stop;
   return(Ask + risk * RiskRewardRatio);
}

//+------------------------------------------------------------------+
//| Calcola confidence segnale                                       |
//+------------------------------------------------------------------+
double CalculateDynamicConfidence(double stopLoss, double takeProfit)
{
   double risk   = Ask - stopLoss;
   double reward = takeProfit - Ask;
   double rr     = risk>0 ? reward/risk : 0.0;
   // normalizzazione R:R su un massimo considerato di 5: da 0–1
   double rrScore = MathMin(rr/5.0, 1.0);

   // RSI: più rsi è sotto la soglia oversold, più score
   double rsi       = iRSI(NULL,0,RSI_Period,PRICE_CLOSE,0);
   double rsiScore  = (RSI_Oversold - rsi) / RSI_Oversold;
   rsiScore = MathMax(0.0, MathMin(rsiScore,1.0));


   // media
   double conf = 0.5*rrScore + 0.5*rsiScore;
   return NormalizeDouble(conf, 2);
}


//+------------------------------------------------------------------+
//| Calcola forza basata su quanti indicatori utilizzati             |
//+------------------------------------------------------------------+
double CalculateStrength() {
   int signals = 0;
   
   if(CheckTrend()) signals++;
   if(CheckRSI()) signals++;
   if(CheckBB()) signals++;
   if(CheckVolume()) signals++;
   
   return(signals / 4.0);
}