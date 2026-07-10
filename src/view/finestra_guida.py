"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Finestra di guida che spiega le sezioni principali dell'applicazione,
             richiamabile dal menu Aiuto.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QPushButton, QTextBrowser, QVBoxLayout, QWidget

_CONTENUTO_GUIDA_HTML = """
<h2>Guida di FiscalFlow</h2>
<p>FiscalFlow traccia e proietta l'andamento fiscale delle buste paga (CCNL Metalmeccanici),
calcolando i progressivi mensili e simulando il conguaglio IRPEF di fine anno.</p>

<h3>Caricamento da PDF</h3>
<p>L'unico modo per inserire una busta paga è caricarne il PDF con il pulsante
<b>"Carica da PDF cedolino…"</b>: si possono selezionare uno o più file insieme.
Il testo viene letto interamente in locale (nessun dato lascia il computer, non serve
connessione di rete) e i valori vengono riconosciuti tramite pattern sulle diciture più
comuni dei cedolini italiani. Prima di aggiungere le buste paga in archivio viene sempre
mostrato un riepilogo di conferma; i PDF non riconosciuti vengono segnalati e non vengono
inseriti.</p>

<h3>Tabella dei progressivi</h3>
<p>Mostra, mese per mese, retribuzione lorda, imponibile INPS progressivo, imponibile
fiscale progressivo, tasse pagate progressive, TFR maturato progressivo e netto percepito.
Le colonne si adattano automaticamente al contenuto.</p>

<h3>Proiezione e Conguaglio di Fine Anno</h3>
<p>Stima la Retribuzione Annua Lorda (RAL) di fine anno, la tredicesima e il conguaglio
IRPEF finale (a credito o a debito), calcolando automaticamente le addizionali
regionale/comunale in base al comune di residenza fiscale rilevato nei cedolini.</p>

<h3>Prospetto Fiscale</h3>
<p>Riepiloga i mesi già inseriti nell'anno: totale tasse pagate con l'aliquota media
effettiva, TFR maturato, contributi al fondo Cometa (dipendente, azienda e complessivo),
addizionali, trattenute complessive con la loro incidenza sul lordo, e netto percepito
totale.</p>

<h3>Menu File</h3>
<p><b>Salva archivio…</b> esporta tutte le buste paga inserite in un file JSON;
<b>Apri archivio…</b> le importa nuovamente in una sessione successiva.</p>

<h3>Aggiornamenti</h3>
<p>All'avvio, e in qualsiasi momento da Aiuto → Controlla aggiornamenti, l'app verifica se
è disponibile una versione più recente pubblicata su GitHub. In caso affermativo viene
proposta l'apertura della pagina di download: l'aggiornamento va scaricato e installato
manualmente, non viene sostituito automaticamente l'eseguibile in uso.</p>
"""


class FinestraGuida(QDialog):
    """Finestra modale con la guida alle funzionalità dell'applicazione."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Guida di FiscalFlow")
        self.resize(640, 560)
        self._costruisci_widget()

    def _costruisci_widget(self) -> None:
        visualizzatore = QTextBrowser(self)
        visualizzatore.setOpenExternalLinks(True)
        visualizzatore.setHtml(_CONTENUTO_GUIDA_HTML)

        pulsante_chiudi = QPushButton("Chiudi", self)
        pulsante_chiudi.clicked.connect(self.accept)
        pulsante_chiudi.setDefault(True)

        layout = QVBoxLayout(self)
        layout.addWidget(visualizzatore)
        layout.addWidget(pulsante_chiudi, alignment=Qt.AlignmentFlag.AlignRight)
