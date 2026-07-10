"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Importatore che estrae automaticamente i dati di una busta paga da un file PDF
             di cedolino letto interamente in locale: il testo viene estratto con pypdf e i
             valori numerici vengono riconosciuti tramite espressioni regolari sulle diciture
             più comuni dei cedolini italiani. Nessun dato lascia il computer dell'utente: non
             serve alcuna connessione di rete né una API key.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from pypdf import PdfReader

from .busta_paga import BustaPaga
from .enums import LivelloCCNL, Mese

# Importo in formato italiano: migliaia con punto, decimali con virgola (es. "1.234,56"),
# oppure senza separatore delle migliaia (es. "234,56" o "234"); parentesi o "-" per il segno.
_NUMERO: str = r"-?\(?\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?\)?|-?\(?\d+(?:,\d{1,2})?\)?"

_ETICHETTE_CAMPI: dict[str, tuple[str, ...]] = {
    "totale_elementi_retributivi": (
        "totale competenze",
        "totale elementi retributivi",
        "totale retribuzione",
        "retribuzione lorda",
    ),
    "ore_ordinarie": ("ore ordinarie", "ore lavorate", "ore mensili"),
    "straordinari": ("straordinari", "lavoro straordinario", "ore straordinarie"),
    "fringe_benefit": ("fringe benefit", "benefit aziendali", "welfare aziendale"),
    "contributi_inps_dipendente": (
        "contributi inps",
        "trattenute inps",
        "contr\\. inps dip",
        "inps dipendente",
    ),
    "contributi_cometa_dipendente": (
        "cometa dipendente",
        "fondo cometa dip",
        "previdenza complementare dip",
    ),
    "contributi_cometa_azienda": (
        "cometa azienda",
        "fondo cometa azi",
        "previdenza complementare azi",
    ),
    "irpef_pagata": ("irpef", "ritenute irpef", "imposta netta"),
    "addizionale_regionale_pagata": ("addizionale regionale", "add\\. region", "add\\.reg"),
    "addizionale_comunale_pagata": ("addizionale comunale", "add\\. comun", "add\\.com"),
    "conguaglio_730": ("conguaglio 730", "conguaglio fiscale", "mod\\. 730"),
    "quota_tfr_maturata": ("tfr maturato", "accantonamento tfr", "quota tfr", "t\\.f\\.r\\."),
}

_CAMPI_OBBLIGATORI: tuple[str, ...] = ("mese", "anno", "livello", "totale_elementi_retributivi")


class ErroreImportazionePdf(Exception):
    """Sollevata quando l'estrazione dei dati dal PDF del cedolino non va a buon fine."""


class ImportatorePdfBustaPaga:
    """Estrae localmente, senza alcuna chiamata di rete, i dati di un cedolino da PDF."""

    def estrai_busta_paga(self, percorso_pdf: Path) -> BustaPaga:
        """Legge il PDF del cedolino indicato e restituisce la BustaPaga con i dati estratti."""
        percorso = Path(percorso_pdf)
        if not percorso.is_file():
            raise ErroreImportazionePdf(f"File PDF non trovato: {percorso}")

        testo = self._estrai_testo(percorso)
        if not testo.strip():
            raise ErroreImportazionePdf(
                "Impossibile estrarre testo dal PDF: è probabilmente una scansione immagine "
                "priva di testo selezionabile. Inserisci i dati manualmente."
            )

        dati = self._estrai_dati_da_testo(testo)
        campi_mancanti = [campo for campo in _CAMPI_OBBLIGATORI if dati.get(campo) is None]
        if campi_mancanti:
            raise ErroreImportazionePdf(
                "Non è stato possibile riconoscere nel PDF i seguenti dati obbligatori: "
                f"{', '.join(campi_mancanti)}. Inserisci la busta paga manualmente."
            )

        return self._costruisci_busta_paga(dati)

    @staticmethod
    def _estrai_testo(percorso: Path) -> str:
        try:
            lettore = PdfReader(str(percorso))
            return "\n".join(pagina.extract_text() or "" for pagina in lettore.pages)
        except Exception as errore:  # pypdf non espone un'unica eccezione base stabile
            raise ErroreImportazionePdf(f"Impossibile leggere il file PDF: {errore}") from errore

    @classmethod
    def _estrai_dati_da_testo(cls, testo: str) -> dict[str, object]:
        dati: dict[str, object] = {
            "mese": cls._cerca_mese(testo),
            "anno": cls._cerca_anno(testo),
            "livello": cls._cerca_livello(testo),
            "comune_residenza": cls._cerca_comune(testo),
        }
        for campo, etichette in _ETICHETTE_CAMPI.items():
            dati[campo] = cls._cerca_valore(testo, etichette)
        return dati

    @staticmethod
    def _cerca_valore(testo: str, etichette: Sequence[str]) -> float | None:
        for etichetta in etichette:
            pattern = re.compile(rf"{etichetta}[^\d\-(\n]{{0,25}}({_NUMERO})", re.IGNORECASE)
            corrispondenza = pattern.search(testo)
            if corrispondenza:
                return ImportatorePdfBustaPaga._converti_numero_italiano(corrispondenza.group(1))
        return None

    @staticmethod
    def _converti_numero_italiano(testo: str) -> float:
        grezzo = testo.strip()
        negativo = grezzo.startswith("-") or (grezzo.startswith("(") and grezzo.endswith(")"))
        pulito = grezzo.strip("()-").replace("€", "").strip()
        if "," in pulito:
            pulito = pulito.replace(".", "").replace(",", ".")
        valore = float(pulito)
        return -abs(valore) if negativo else valore

    @staticmethod
    def _cerca_mese(testo: str) -> Mese | None:
        nomi_mesi = {mese.nome_italiano.lower(): mese for mese in Mese}
        corrispondenza = re.search(rf"\b({'|'.join(nomi_mesi)})\b", testo, re.IGNORECASE)
        if corrispondenza:
            return nomi_mesi[corrispondenza.group(1).lower()]

        corrispondenza = re.search(r"\b(0[1-9]|1[0-2])[/\-](?:19|20)\d{2}\b", testo)
        if corrispondenza:
            return Mese(int(corrispondenza.group(1)))
        return None

    @staticmethod
    def _cerca_anno(testo: str) -> int | None:
        corrispondenza = re.search(r"\b(20\d{2})\b", testo)
        return int(corrispondenza.group(1)) if corrispondenza else None

    @staticmethod
    def _cerca_livello(testo: str) -> LivelloCCNL | None:
        codici = "|".join(livello.value for livello in LivelloCCNL)
        corrispondenza = re.search(
            rf"(?:livello|qualifica|categoria|inquadramento)\D{{0,20}}\b({codici})\b",
            testo,
            re.IGNORECASE,
        )
        if not corrispondenza:
            corrispondenza = re.search(rf"\b({codici})\b", testo)
        if not corrispondenza:
            return None
        try:
            return LivelloCCNL(corrispondenza.group(1).upper())
        except ValueError:
            return None

    @staticmethod
    def _cerca_comune(testo: str) -> str:
        corrispondenza = re.search(
            r"(?:comune di residenza|residenza fiscale|comune)\s*[:\-]?\s*([A-ZÀ-Ü][A-Za-zà-ü' ]{2,30})",
            testo,
            re.IGNORECASE,
        )
        return corrispondenza.group(1).strip() if corrispondenza else ""

    @staticmethod
    def _costruisci_busta_paga(dati: dict[str, object]) -> BustaPaga:
        return BustaPaga(
            mese=dati["mese"],  # type: ignore[arg-type]
            anno=int(dati["anno"]),  # type: ignore[arg-type]
            livello=dati["livello"],  # type: ignore[arg-type]
            totale_elementi_retributivi=float(dati["totale_elementi_retributivi"]),  # type: ignore[arg-type]
            comune_residenza=str(dati.get("comune_residenza") or ""),
            ore_ordinarie=float(dati.get("ore_ordinarie") or 0.0),
            straordinari=float(dati.get("straordinari") or 0.0),
            fringe_benefit=float(dati.get("fringe_benefit") or 0.0),
            contributi_inps_dipendente=float(dati.get("contributi_inps_dipendente") or 0.0),
            contributi_cometa_dipendente=float(dati.get("contributi_cometa_dipendente") or 0.0),
            contributi_cometa_azienda=float(dati.get("contributi_cometa_azienda") or 0.0),
            irpef_pagata=float(dati.get("irpef_pagata") or 0.0),
            addizionale_regionale_pagata=float(dati.get("addizionale_regionale_pagata") or 0.0),
            addizionale_comunale_pagata=float(dati.get("addizionale_comunale_pagata") or 0.0),
            conguaglio_730=float(dati.get("conguaglio_730") or 0.0),
            quota_tfr_maturata=float(dati.get("quota_tfr_maturata") or 0.0),
        )
