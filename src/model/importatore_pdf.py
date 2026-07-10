"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Importatore che estrae automaticamente i dati di una busta paga da un file PDF
             (cedolino) tramite l'API multimodale di Gemini (google-genai), restituendo
             direttamente un oggetto BustaPaga pronto per l'inserimento in archivio.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from google import genai
from google.genai import types

from .busta_paga import BustaPaga
from .enums import LivelloCCNL, Mese

_MODELLO_GEMINI: str = "gemini-2.5-flash"

_PROMPT_ESTRAZIONE: str = (
    "Analizza il cedolino paga (busta paga italiana) allegato in formato PDF ed estrai i dati "
    "richiesti dallo schema JSON fornito, leggendoli esattamente come riportati nel documento. "
    "Usa 0 per gli importi non presenti o non applicabili nel cedolino. "
    f"Il livello di inquadramento CCNL deve essere uno tra: {', '.join(l.value for l in LivelloCCNL)}. "
    "Il mese di competenza va espresso come numero da 1 (gennaio) a 12 (dicembre)."
)

_SCHEMA_RISPOSTA: dict = {
    "type": "object",
    "properties": {
        "mese": {"type": "integer", "minimum": 1, "maximum": 12},
        "anno": {"type": "integer"},
        "livello": {"type": "string", "enum": [livello.value for livello in LivelloCCNL]},
        "comune_residenza": {"type": "string"},
        "totale_elementi_retributivi": {"type": "number"},
        "ore_ordinarie": {"type": "number"},
        "straordinari": {"type": "number"},
        "fringe_benefit": {"type": "number"},
        "contributi_inps_dipendente": {"type": "number"},
        "contributi_cometa_dipendente": {"type": "number"},
        "contributi_cometa_azienda": {"type": "number"},
        "irpef_pagata": {"type": "number"},
        "addizionale_regionale_pagata": {"type": "number"},
        "addizionale_comunale_pagata": {"type": "number"},
        "conguaglio_730": {"type": "number"},
    },
    "required": ["mese", "anno", "livello", "totale_elementi_retributivi"],
}


class ErroreImportazionePdf(Exception):
    """Sollevata quando l'estrazione dei dati dal PDF del cedolino non va a buon fine."""


class ImportatorePdfBustaPaga:
    """Estrae i dati di una busta paga mensile da un PDF di cedolino tramite Gemini."""

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def estrai_busta_paga(self, percorso_pdf: Path) -> BustaPaga:
        """Legge il PDF del cedolino indicato e restituisce la BustaPaga con i dati estratti."""
        if not self._api_key:
            raise ErroreImportazionePdf(
                "Nessuna API key di Gemini configurata. Imposta la variabile d'ambiente "
                "GEMINI_API_KEY con una chiave valida per abilitare il caricamento da PDF."
            )

        percorso = Path(percorso_pdf)
        if not percorso.is_file():
            raise ErroreImportazionePdf(f"File PDF non trovato: {percorso}")

        try:
            contenuto_pdf = percorso.read_bytes()
        except OSError as errore:
            raise ErroreImportazionePdf(f"Impossibile leggere il file PDF: {errore}") from errore

        testo_risposta = self._interroga_gemini(contenuto_pdf)

        try:
            dati = json.loads(testo_risposta)
        except json.JSONDecodeError as errore:
            raise ErroreImportazionePdf(f"Risposta del modello non interpretabile: {errore}") from errore

        return self._costruisci_busta_paga(dati)

    def _interroga_gemini(self, contenuto_pdf: bytes) -> str:
        try:
            client = genai.Client(api_key=self._api_key)
            risposta = client.models.generate_content(
                model=_MODELLO_GEMINI,
                contents=[
                    types.Part.from_bytes(data=contenuto_pdf, mime_type="application/pdf"),
                    _PROMPT_ESTRAZIONE,
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_SCHEMA_RISPOSTA,
                ),
            )
        except Exception as errore:  # le eccezioni della SDK non sono tipizzate in modo stabile
            raise ErroreImportazionePdf(f"Estrazione dati dal PDF fallita: {errore}") from errore

        testo_risposta = (risposta.text or "").strip()
        if not testo_risposta:
            raise ErroreImportazionePdf("Il modello non ha restituito alcun dato dal PDF caricato.")
        return testo_risposta

    @staticmethod
    def _costruisci_busta_paga(dati: dict) -> BustaPaga:
        """Converte il dizionario estratto dal modello in un oggetto BustaPaga validato."""
        try:
            mese = Mese(int(dati["mese"]))
            anno = int(dati["anno"])
            livello = LivelloCCNL(dati["livello"])
            totale_elementi_retributivi = float(dati["totale_elementi_retributivi"])
        except (KeyError, ValueError) as errore:
            raise ErroreImportazionePdf(
                f"Dati estratti dal PDF incompleti o non validi: {errore}"
            ) from errore

        return BustaPaga(
            mese=mese,
            anno=anno,
            livello=livello,
            totale_elementi_retributivi=totale_elementi_retributivi,
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
        )
