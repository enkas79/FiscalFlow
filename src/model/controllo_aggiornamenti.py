"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Verifica se è disponibile una versione più recente di FiscalFlow confrontando
             quella installata con l'ultima release pubblicata su GitHub (pubblicate
             automaticamente dalla pipeline CI ad ogni incremento di VERSION.txt).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass

_URL_ULTIMA_RELEASE = "https://api.github.com/repos/enkas79/FiscalFlow/releases/latest"
_TIMEOUT_SECONDI = 5


class ErroreControlloAggiornamenti(Exception):
    """Sollevata quando non è possibile verificare la disponibilità di aggiornamenti."""


@dataclass(frozen=True, slots=True)
class InformazioniAggiornamento:
    """Esito del confronto tra la versione installata e l'ultima release pubblicata."""

    versione_installata: str
    versione_disponibile: str
    url_release: str

    @property
    def aggiornamento_disponibile(self) -> bool:
        return _versione_a_tupla(self.versione_disponibile) > _versione_a_tupla(self.versione_installata)


def _versione_a_tupla(versione: str) -> tuple[int, ...]:
    """Converte una stringa di versione (es. "v1.2.3" o "1.2") in una tupla confrontabile."""
    normalizzata = versione.strip().lstrip("vV")
    parti: list[int] = []
    for pezzo in normalizzata.split("."):
        cifre = "".join(carattere for carattere in pezzo if carattere.isdigit())
        parti.append(int(cifre) if cifre else 0)
    return tuple(parti) if parti else (0,)


def verifica_aggiornamento_disponibile(versione_installata: str) -> InformazioniAggiornamento:
    """Interroga l'ultima GitHub Release di FiscalFlow e la confronta con quella installata."""
    richiesta = urllib.request.Request(
        _URL_ULTIMA_RELEASE, headers={"Accept": "application/vnd.github+json"}
    )
    try:
        with urllib.request.urlopen(richiesta, timeout=_TIMEOUT_SECONDI) as risposta:
            dati = json.loads(risposta.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError) as errore:
        raise ErroreControlloAggiornamenti(
            f"Impossibile contattare GitHub per verificare gli aggiornamenti: {errore}"
        ) from errore
    except json.JSONDecodeError as errore:
        raise ErroreControlloAggiornamenti(f"Risposta di GitHub non interpretabile: {errore}") from errore

    tag = dati.get("tag_name")
    if not tag:
        raise ErroreControlloAggiornamenti("La release più recente non contiene un numero di versione valido.")

    return InformazioniAggiornamento(
        versione_installata=versione_installata,
        versione_disponibile=tag,
        url_release=dati.get("html_url") or _URL_ULTIMA_RELEASE,
    )
