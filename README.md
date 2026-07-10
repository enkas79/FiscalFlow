# FiscalFlow
FiscalFlow è un'app desktop OOP in Python e PyQt6 per tracciare e proiettare l'andamento fiscale delle buste paga (CCNL Metalmeccanici). Mappando i cedolini mensili, calcola i progressivi e simula la RAL di fine anno includendo variazioni di livello e tredicesima, anticipando l'esatto conguaglio IRPEF a credito o a debito a dicembre.

## Caricamento del cedolino da PDF
I dati della busta paga mensile si inseriscono caricando il PDF del cedolino: il pulsante "Carica da PDF cedolino…" analizza il documento tramite l'API multimodale di Gemini (`google-genai`) e compila automaticamente i campi del form, che restano modificabili per una verifica prima di confermare con "Aggiungi busta paga".

Per abilitare l'importazione è necessaria una API key di Gemini, da impostare nella variabile d'ambiente `GEMINI_API_KEY` (in alternativa è accettata anche `GOOGLE_API_KEY`).
