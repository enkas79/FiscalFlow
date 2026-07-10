# FiscalFlow
FiscalFlow è un'app desktop OOP in Python e PyQt6 per tracciare e proiettare l'andamento fiscale delle buste paga (CCNL Metalmeccanici). Mappando i cedolini mensili, calcola i progressivi e simula la RAL di fine anno includendo variazioni di livello e tredicesima, anticipando l'esatto conguaglio IRPEF a credito o a debito a dicembre.

## Caricamento del cedolino da PDF
L'unico modo per inserire una busta paga è caricare il PDF del cedolino: non ci sono campi di compilazione manuale. Il pulsante "Carica da PDF cedolino…" permette di selezionare uno o più PDF, estrae il testo in locale con `pypdf` e ne riconosce i valori tramite pattern sulle diciture più comuni dei cedolini italiani (incluso il tracciato Zucchetti, molto diffuso). Nessun dato lascia il computer: non serve alcuna connessione di rete né una API key.

Dopo l'elaborazione viene sempre mostrato un riepilogo di conferma (mese, anno, livello, retribuzione riconosciuti) prima di aggiungere le buste paga in archivio; i file non riconosciuti vengono segnalati e non vengono inseriti.

L'estrazione è euristica: su cedolini con layout molto diversi da quello atteso, o generati da scansioni immagine, alcuni campi potrebbero non essere riconosciuti — in tal caso il relativo PDF va controllato manualmente, dato che l'app non offre più un inserimento a mano.

## Prospetto Fiscale
Il pannello "Prospetto Fiscale" riepiloga i mesi inseriti nell'anno: totale tasse pagate con la relativa aliquota media effettiva, TFR maturato, contributi al fondo Cometa (dipendente, azienda e complessivo), addizionali regionale/comunale, trattenute complessive (INPS + Cometa dipendente + tasse) con la loro incidenza sul lordo, e netto percepito totale.
