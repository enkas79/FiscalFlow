"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Finestra principale dell'applicazione: assembla il pannello di caricamento PDF,
             la tabella dei progressivi mensili, i pannelli di proiezione/conguaglio e
             prospetto fiscale, la barra dei menù (File/Aiuto) e il controllo aggiornamenti.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QAction, QDesktopServices, QKeySequence
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ..model.controllo_aggiornamenti import (
    ErroreControlloAggiornamenti,
    InformazioniAggiornamento,
    verifica_aggiornamento_disponibile,
)
from ..versione import get_versione
from .finestra_guida import FinestraGuida
from .form_inserimento import FormInserimentoBustaPaga
from .pannello_proiezione import PannelloProiezioneConguaglio
from .prospetto_fiscale import PannelloProspettoFiscale
from .tabella_riepilogo import TabellaRiepilogoBustePaga

_URL_REPOSITORY = "https://github.com/enkas79/FiscalFlow"


class _ThreadControlloAggiornamenti(QThread):
    """Esegue il controllo aggiornamenti in background per non bloccare l'interfaccia."""

    trovato = pyqtSignal(object)
    fallito = pyqtSignal(str)

    def __init__(self, versione_installata: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._versione_installata = versione_installata

    def run(self) -> None:
        try:
            info = verifica_aggiornamento_disponibile(self._versione_installata)
        except ErroreControlloAggiornamenti as errore:
            self.fallito.emit(str(errore))
            return
        self.trovato.emit(info)


class MainWindow(QMainWindow):
    """Finestra principale dell'applicazione FiscalFlow."""

    richiesta_salvataggio_archivio = pyqtSignal(Path)
    richiesta_apertura_archivio = pyqtSignal(Path)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"FiscalFlow v{get_versione()} - Proiezione Fiscale Buste Paga")
        self.resize(1280, 820)

        self.form_inserimento = FormInserimentoBustaPaga(self)
        self.tabella_riepilogo = TabellaRiepilogoBustePaga(self)
        self.pannello_proiezione = PannelloProiezioneConguaglio(self)
        self.pannello_prospetto = PannelloProspettoFiscale(self)

        self._thread_aggiornamenti: _ThreadControlloAggiornamenti | None = None

        self._costruisci_layout()
        self._costruisci_menu()
        self._avvia_controllo_aggiornamenti(silenzioso=True)

    def _costruisci_layout(self) -> None:
        contenitore_centrale = QWidget(self)
        layout_principale = QVBoxLayout(contenitore_centrale)
        layout_principale.setContentsMargins(12, 12, 12, 12)
        layout_principale.setSpacing(12)

        layout_principale.addWidget(self.form_inserimento, stretch=0)
        layout_principale.addWidget(self.tabella_riepilogo, stretch=1)

        layout_riepiloghi = QHBoxLayout()
        layout_riepiloghi.setSpacing(12)
        layout_riepiloghi.addWidget(self.pannello_proiezione, stretch=1)
        layout_riepiloghi.addWidget(self.pannello_prospetto, stretch=1)
        layout_principale.addLayout(layout_riepiloghi, stretch=0)

        self.setCentralWidget(contenitore_centrale)

    def _costruisci_menu(self) -> None:
        menu_file = self.menuBar().addMenu("&File")

        azione_salva = QAction("&Salva archivio…", self)
        azione_salva.setShortcut(QKeySequence.StandardKey.Save)
        azione_salva.triggered.connect(self._gestisci_salva_archivio)
        menu_file.addAction(azione_salva)

        azione_apri = QAction("&Apri archivio…", self)
        azione_apri.setShortcut(QKeySequence.StandardKey.Open)
        azione_apri.triggered.connect(self._gestisci_apri_archivio)
        menu_file.addAction(azione_apri)

        menu_file.addSeparator()

        azione_esci = QAction("&Esci", self)
        azione_esci.setShortcut(QKeySequence.StandardKey.Quit)
        azione_esci.triggered.connect(self.close)
        menu_file.addAction(azione_esci)

        menu_aiuto = self.menuBar().addMenu("&Aiuto")

        azione_guida = QAction("&Guida", self)
        azione_guida.setShortcut(QKeySequence.StandardKey.HelpContents)
        azione_guida.triggered.connect(self._gestisci_apri_guida)
        menu_aiuto.addAction(azione_guida)

        azione_aggiornamenti = QAction("&Controlla aggiornamenti…", self)
        azione_aggiornamenti.triggered.connect(lambda: self._avvia_controllo_aggiornamenti(silenzioso=False))
        menu_aiuto.addAction(azione_aggiornamenti)

        menu_aiuto.addSeparator()

        azione_info = QAction("&Informazioni su FiscalFlow", self)
        azione_info.triggered.connect(self._gestisci_apri_informazioni)
        menu_aiuto.addAction(azione_info)

    # ------------------------------------------------------------------
    # File: salvataggio/apertura archivio
    # ------------------------------------------------------------------

    def _gestisci_salva_archivio(self) -> None:
        percorso_scelto, _ = QFileDialog.getSaveFileName(
            self, "Salva archivio buste paga", "fiscalflow_archivio.json", "File JSON (*.json)"
        )
        if percorso_scelto:
            self.richiesta_salvataggio_archivio.emit(Path(percorso_scelto))

    def _gestisci_apri_archivio(self) -> None:
        percorso_scelto, _ = QFileDialog.getOpenFileName(
            self, "Apri archivio buste paga", "", "File JSON (*.json)"
        )
        if percorso_scelto:
            self.richiesta_apertura_archivio.emit(Path(percorso_scelto))

    # ------------------------------------------------------------------
    # Aiuto: guida, informazioni, aggiornamenti
    # ------------------------------------------------------------------

    def _gestisci_apri_guida(self) -> None:
        FinestraGuida(self).exec()

    def _gestisci_apri_informazioni(self) -> None:
        QMessageBox.about(
            self,
            "Informazioni su FiscalFlow",
            f"<h3>FiscalFlow</h3>"
            f"<p>Versione {get_versione()}</p>"
            f"<p>App desktop per tracciare e proiettare l'andamento fiscale delle buste "
            f"paga (CCNL Metalmeccanici), con importazione automatica dei cedolini da PDF "
            f"e calcolo del conguaglio IRPEF di fine anno.</p>"
            f"<p>Autore: Enrico Martini</p>"
            f"<p><a href='{_URL_REPOSITORY}'>{_URL_REPOSITORY}</a></p>",
        )

    def _avvia_controllo_aggiornamenti(self, *, silenzioso: bool) -> None:
        if self._thread_aggiornamenti is not None and self._thread_aggiornamenti.isRunning():
            return

        # Nessun parent Qt: il thread non deve dipendere dal ciclo di vita della finestra,
        # altrimenti la chiusura dell'app mentre la verifica di rete è ancora in corso
        # solleverebbe "QThread: Destroyed while thread is still running". Si autodistrugge
        # a fine esecuzione tramite finished/deleteLater; closeEvent scollega i segnali verso
        # la finestra se questa viene chiusa prima che il controllo sia terminato.
        thread = _ThreadControlloAggiornamenti(get_versione())
        thread.trovato.connect(lambda info: self._gestisci_esito_controllo_aggiornamenti(info, silenzioso))
        thread.fallito.connect(lambda errore: self._gestisci_errore_controllo_aggiornamenti(errore, silenzioso))
        thread.finished.connect(thread.deleteLater)
        self._thread_aggiornamenti = thread
        thread.start()

    def closeEvent(self, event) -> None:  # noqa: N802 (nome imposto da Qt)
        if self._thread_aggiornamenti is not None:
            try:
                self._thread_aggiornamenti.trovato.disconnect()
                self._thread_aggiornamenti.fallito.disconnect()
            except TypeError:
                pass  # nessuno slot collegato (controllo già concluso)
            except RuntimeError:
                pass  # l'oggetto thread si è già autodistrutto (deleteLater) a controllo concluso
        super().closeEvent(event)

    def _gestisci_esito_controllo_aggiornamenti(
        self, info: InformazioniAggiornamento, silenzioso: bool
    ) -> None:
        if not info.aggiornamento_disponibile:
            if not silenzioso:
                QMessageBox.information(
                    self,
                    "Controllo aggiornamenti",
                    f"Stai già usando l'ultima versione disponibile (v{info.versione_installata}).",
                )
            return

        risposta = QMessageBox.question(
            self,
            "Aggiornamento disponibile",
            f"È disponibile FiscalFlow {info.versione_disponibile} "
            f"(versione installata: v{info.versione_installata}).\n\n"
            "Vuoi aprire la pagina di download? L'aggiornamento va scaricato e installato "
            "manualmente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if risposta == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl(info.url_release))

    def _gestisci_errore_controllo_aggiornamenti(self, messaggio: str, silenzioso: bool) -> None:
        if not silenzioso:
            QMessageBox.warning(self, "Controllo aggiornamenti", messaggio)
