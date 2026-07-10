"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Importatore che estrae automaticamente i dati di una busta paga da uno o più
             PDF di cedolino letti interamente in locale: il testo viene estratto con pypdf
             e i valori numerici vengono riconosciuti tramite espressioni regolari calibrate
             sulle diciture dei cedolini italiani (in particolare il tracciato Zucchetti,
             molto diffuso). Nessun dato lascia il computer dell'utente: non serve alcuna
             connessione di rete né una API key.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from pypdf import PdfReader

from .busta_paga import BustaPaga
from .enums import LivelloCCNL, Mese

# Importo in formato italiano: migliaia con punto, decimali con virgola (es. "1.234,56"),
# oppure senza separatore delle migliaia e con un numero di decimali variabile, come talvolta
# capita per le aliquote (es. "2158,26" o "9,190"); parentesi o "-" per il segno.
_NUMERO: str = (
    r"-?\(?\d{1,3}(?:\.\d{3})+(?:,\d{1,3})?\)?"
    r"|-?\(?\d+,\d{1,3}\)?"
    r"|-?\(?\d+\)?"
)

# Etichette di importi che compaiono una sola volta per mese e nella forma "etichetta ... numero"
# entro pochi caratteri: valide sia sul tracciato Zucchetti sia su diciture generiche.
_ETICHETTE_SINGOLE: dict[str, tuple[str, ...]] = {
    "ore_ordinarie": ("ore ordinarie", "ore lavorate", "ore mensili"),
    "fringe_benefit": ("fringe benefit", "benefit aziendali", "welfare aziendale"),
    "conguaglio_730": ("conguaglio 730", "conguaglio fiscale", "mod\\. 730"),
}

# Etichette di importi che possono comparire su più righe nello stesso mese (es. addizionale
# comunale versata in più rate, o più voci di straordinario) e vanno sommate. Ogni campo
# elenca uno o più gruppi di parole chiave: una riga corrisponde se contiene TUTTE le parole
# di ALMENO UN gruppo (le parole di un gruppo non devono essere adiacenti).
_ETICHETTE_DA_SOMMARE: dict[str, tuple[tuple[str, ...], ...]] = {
    "straordinari": (("straordinario",), ("straordinari",), ("lavoro straordinario",)),
    "contributi_inps_dipendente": (("inps", "c/dip"), ("inps", "dipendente"), ("trattenute inps",)),
    "contributi_cometa_dipendente": (("cometa", "c/dip"), ("cometa", "dipendente")),
    "contributi_cometa_azienda": (("cometa", "c/azi"), ("cometa", "azienda")),
    "addizionale_regionale_pagata": (("addizionale", "regionale"),),
    "addizionale_comunale_pagata": (("addizionale", "comunale"),),
    "quota_tfr_maturata": (("tfr", "cometa"), ("tfr", "maturat"), ("accantonamento", "tfr")),
}

_CAMPI_OBBLIGATORI: tuple[str, ...] = ("mese", "anno", "livello", "totale_elementi_retributivi")


class ErroreImportazionePdf(Exception):
    """Sollevata quando l'estrazione dei dati dal PDF del cedolino non va a buon fine."""


class ImportatorePdfBustaPaga:
    """Estrae localmente, senza alcuna chiamata di rete, i dati di uno o più cedolini da PDF."""

    def estrai_buste_paga(self, percorsi_pdf: Sequence[Path]) -> tuple[list[BustaPaga], list[tuple[Path, str]]]:
        """
        Elabora più PDF in un colpo solo: restituisce le buste paga riconosciute (ordinate
        cronologicamente) e la lista di (percorso, messaggio d'errore) per i file non
        riconosciuti, da inserire manualmente.
        """
        importate: list[BustaPaga] = []
        errori: list[tuple[Path, str]] = []
        for percorso in percorsi_pdf:
            try:
                importate.append(self.estrai_busta_paga(percorso))
            except ErroreImportazionePdf as errore:
                errori.append((Path(percorso), str(errore)))
        importate.sort(key=lambda busta: busta.chiave_periodo)
        return importate, errori

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
        mese, anno = cls._cerca_mese_anno(testo)
        dati: dict[str, object] = {
            "mese": mese,
            "anno": anno,
            "livello": cls._cerca_livello(testo),
            "comune_residenza": cls._cerca_comune(testo),
            "totale_elementi_retributivi": cls._cerca_totale_retributivo(testo),
            "irpef_pagata": cls._cerca_irpef_pagata(testo),
        }
        for campo, etichette in _ETICHETTE_SINGOLE.items():
            dati[campo] = cls._cerca_valore(testo, etichette)
        for campo, chiavi in _ETICHETTE_DA_SOMMARE.items():
            dati[campo] = cls._somma_righe(testo, chiavi)
        return dati

    # ------------------------------------------------------------------
    # Ricerca di un singolo valore (prima etichetta trovata, primo numero successivo)
    # ------------------------------------------------------------------

    @staticmethod
    def _cerca_valore(testo: str, etichette: Sequence[str]) -> float | None:
        for etichetta in etichette:
            pattern = re.compile(rf"{etichetta}[^\d\-(\n]{{0,25}}({_NUMERO})", re.IGNORECASE)
            corrispondenza = pattern.search(testo)
            if corrispondenza:
                return ImportatorePdfBustaPaga._converti_numero_italiano(corrispondenza.group(1))
        return None

    # ------------------------------------------------------------------
    # Somma dell'ultimo numero di ogni riga che contiene tutte le chiavi indicate: utile per
    # voci che possono comparire più volte nello stesso mese (es. rate di addizionali, più
    # righe di straordinario, contributi INPS su più codici).
    # ------------------------------------------------------------------

    @staticmethod
    def _somma_righe(testo: str, gruppi_chiavi: Sequence[Sequence[str]]) -> float | None:
        totale: float | None = None
        for riga in testo.splitlines():
            riga_minuscola = riga.lower()
            corrisponde = any(
                all(
                    re.search(rf"(?<![a-z0-9]){re.escape(chiave)}", riga_minuscola)
                    for chiave in gruppo
                )
                for gruppo in gruppi_chiavi
            )
            if not corrisponde:
                continue
            numeri = re.findall(_NUMERO, riga)
            if not numeri:
                continue
            valore = ImportatorePdfBustaPaga._converti_numero_italiano(numeri[-1])
            totale = valore if totale is None else totale + valore
        return round(totale, 2) if totale is not None else None

    @staticmethod
    def _converti_numero_italiano(testo: str) -> float:
        grezzo = testo.strip()
        negativo = grezzo.startswith("-") or (grezzo.startswith("(") and grezzo.endswith(")"))
        pulito = grezzo.strip("()-").replace("€", "").strip()
        if "," in pulito:
            pulito = pulito.replace(".", "").replace(",", ".")
        valore = float(pulito)
        return -abs(valore) if negativo else valore

    # ------------------------------------------------------------------
    # Campi con un'estrazione dedicata perché non seguono lo schema "etichetta + numero"
    # ------------------------------------------------------------------

    @staticmethod
    def _cerca_mese_anno(testo: str) -> tuple[Mese | None, int | None]:
        nomi_mesi = {mese.nome_italiano.lower(): mese for mese in Mese}
        # Strategia primaria: nome del mese seguito a breve distanza dall'anno (come nel
        # "periodo di retribuzione" del cedolino, es. "Gennaio   2026").
        corrispondenza = re.search(
            rf"\b({'|'.join(nomi_mesi)})\b\s+(20\d{{2}})\b", testo, re.IGNORECASE
        )
        if corrispondenza:
            return nomi_mesi[corrispondenza.group(1).lower()], int(corrispondenza.group(2))

        corrispondenza = re.search(r"\b(0[1-9]|1[0-2])[/\-](20\d{2})\b", testo)
        if corrispondenza:
            return Mese(int(corrispondenza.group(1))), int(corrispondenza.group(2))

        # Fallback: mese e anno cercati indipendentemente in tutto il documento.
        mese_trovato = None
        corrispondenza_mese = re.search(rf"\b({'|'.join(nomi_mesi)})\b", testo, re.IGNORECASE)
        if corrispondenza_mese:
            mese_trovato = nomi_mesi[corrispondenza_mese.group(1).lower()]

        anno_trovato = None
        corrispondenza_anno = re.search(r"\b(20\d{2})\b", testo)
        if corrispondenza_anno:
            anno_trovato = int(corrispondenza_anno.group(1))

        return mese_trovato, anno_trovato

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
        # Strategia primaria: sui cedolini che calcolano l'addizionale comunale, il nome del
        # comune usato per il calcolo compare da solo sulla riga subito dopo l'ultima rata.
        corrispondenza = re.search(
            r"addizionale comunale[^\n]*\n\s*([A-ZÀ-Ù][A-ZÀ-Ù' ]{2,30})\s*\n",
            testo,
            re.IGNORECASE,
        )
        if corrispondenza:
            return corrispondenza.group(1).strip().title()

        # Fallback: indirizzo in formato "CAP COMUNE (PROV)"; nei cedolini a più pagine
        # compare sia per l'azienda sia per il dipendente, quindi si usa l'ultima occorrenza
        # (l'indirizzo del dipendente, elencato dopo quello dell'azienda).
        corrispondenze_indirizzo = re.findall(
            r"\b\d{5}\s+([A-ZÀ-Ù][A-Za-zà-ù' ]{2,30})\s*\(([A-Z]{2})\)", testo
        )
        if corrispondenze_indirizzo:
            return corrispondenze_indirizzo[-1][0].strip().title()

        # Fallback generico per diciture non standard.
        corrispondenza = re.search(
            r"(?:comune di residenza|residenza fiscale|comune)\s*[:\-]?\s*([A-ZÀ-Ü][A-Za-zà-ü' ]{2,30})",
            testo,
            re.IGNORECASE,
        )
        return corrispondenza.group(1).strip() if corrispondenza else ""

    @staticmethod
    def _cerca_totale_retributivo(testo: str) -> float | None:
        # Diciture generiche più esplicite, se presenti (non tutti i tracciati usano quella
        # Zucchetti "Minimo retr.").
        valore = ImportatorePdfBustaPaga._cerca_valore(
            testo,
            (
                "totale competenze",
                "totale elementi retributivi",
                "totale retribuzione",
                "retribuzione lorda",
            ),
        )
        if valore is not None:
            return valore

        # Tracciato Zucchetti: il totale degli elementi fissi (paga base, scatti,
        # superminimo, ecc.) compare da solo su una riga subito dopo il blocco "Minimo
        # retr. ... Scatti ... Professionalità ...", prima della sezione "SCATTI :"/voci.
        corrispondenza_inizio = re.search(r"minimo retr\.", testo, re.IGNORECASE)
        if not corrispondenza_inizio:
            return None
        finestra = testo[corrispondenza_inizio.end() : corrispondenza_inizio.end() + 500]
        corrispondenza_totale = re.search(rf"\n[ \t]*({_NUMERO})[ \t]*\n", finestra)
        return (
            ImportatorePdfBustaPaga._converti_numero_italiano(corrispondenza_totale.group(1))
            if corrispondenza_totale
            else None
        )

    @staticmethod
    def _cerca_irpef_pagata(testo: str) -> float | None:
        # Diciture generiche più esplicite, se presenti.
        valore = ImportatorePdfBustaPaga._cerca_valore(testo, ("irpef", "ritenute irpef", "imposta netta"))
        if valore is not None:
            return valore

        # Tracciato Zucchetti: "IRPEF" non compare mai come etichetta letterale. L'imposta
        # netta trattenuta nel mese è l'ultimo numero della riga "IMPOSTA LORDA / DETR. ... /
        # IMPOSTA NETTA", che è sempre la terzultima riga non vuota prima del netto in busta
        # (contrassegnato da una sequenza di asterischi, es. "****1953,00").
        corrispondenza_netto = re.search(r"\*{2,}\s*[\d.]+,\d{2}", testo)
        if not corrispondenza_netto:
            return None
        righe_precedenti = [
            riga for riga in testo[: corrispondenza_netto.start()].splitlines() if riga.strip()
        ][-3:]
        if not righe_precedenti:
            return None
        numeri = re.findall(_NUMERO, righe_precedenti[0])
        return ImportatorePdfBustaPaga._converti_numero_italiano(numeri[-1]) if numeri else None

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
