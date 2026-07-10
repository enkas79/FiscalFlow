# FiscalFlow
FiscalFlow è un'app desktop OOP in Python e PyQt6 per tracciare e proiettare l'andamento fiscale delle buste paga (CCNL Metalmeccanici). Mappando i cedolini mensili, calcola i progressivi e simula la RAL di fine anno includendo variazioni di livello e tredicesima, anticipando l'esatto conguaglio IRPEF a credito o a debito a dicembre.

## Caricamento del cedolino da PDF
I dati della busta paga mensile si inseriscono caricando il PDF del cedolino: il pulsante "Carica da PDF cedolino…" estrae il testo in locale con `pypdf` e ne riconosce i valori tramite pattern sulle diciture più comuni dei cedolini italiani (incluso il tracciato Zucchetti, molto diffuso), compilando automaticamente i campi del form. Nessun dato lascia il computer: non serve alcuna connessione di rete né una API key.

- **Un solo PDF selezionato**: i campi del form si compilano per la verifica, da confermare con "Aggiungi busta paga".
- **Più PDF selezionati insieme**: vengono elaborati tutti, e dopo un riepilogo di conferma le buste paga riconosciute vengono aggiunte in blocco; i file non riconosciuti vengono segnalati per l'inserimento manuale.

L'estrazione è euristica: su cedolini con layout molto diversi da quello atteso, o generati da scansioni immagine, alcuni campi potrebbero non essere riconosciuti e vanno completati a mano. Il comune di residenza fiscale è un campo libero (con alcuni comuni capoluogo suggeriti): può essere digitato qualsiasi comune, anche non presente in elenco.

## Prospetto Fiscale
Il pannello "Prospetto Fiscale" riepiloga i mesi inseriti nell'anno: totale tasse pagate con la relativa aliquota media effettiva, TFR maturato, contributi al fondo Cometa (dipendente, azienda e complessivo), addizionali regionale/comunale, trattenute complessive (INPS + Cometa dipendente + tasse) con la loro incidenza sul lordo, e netto percepito totale.
