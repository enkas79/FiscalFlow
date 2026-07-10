"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Test unitari per il controllo aggiornamenti: confronto delle versioni e
             gestione degli errori di rete/risposta, senza contattare GitHub davvero
             (la chiamata HTTP viene simulata).
"""

from __future__ import annotations

import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from src.model.controllo_aggiornamenti import (
    ErroreControlloAggiornamenti,
    verifica_aggiornamento_disponibile,
)


def _risposta_finta(payload: dict) -> MagicMock:
    contesto = MagicMock()
    contesto.__enter__.return_value.read.return_value = json.dumps(payload).encode("utf-8")
    return contesto


def test_rileva_aggiornamento_disponibile() -> None:
    with patch("urllib.request.urlopen", return_value=_risposta_finta(
        {"tag_name": "v0.2.0", "html_url": "https://github.com/enkas79/FiscalFlow/releases/tag/v0.2.0"}
    )):
        info = verifica_aggiornamento_disponibile("0.0.2")

    assert info.aggiornamento_disponibile is True
    assert info.versione_disponibile == "v0.2.0"
    assert info.url_release.endswith("v0.2.0")


def test_nessun_aggiornamento_se_stessa_versione() -> None:
    with patch("urllib.request.urlopen", return_value=_risposta_finta({"tag_name": "v0.0.2"})):
        info = verifica_aggiornamento_disponibile("0.0.2")

    assert info.aggiornamento_disponibile is False


def test_nessun_aggiornamento_se_versione_installata_piu_recente() -> None:
    with patch("urllib.request.urlopen", return_value=_risposta_finta({"tag_name": "v0.0.1"})):
        info = verifica_aggiornamento_disponibile("0.5.0")

    assert info.aggiornamento_disponibile is False


def test_solleva_errore_su_problema_di_rete() -> None:
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("dns failure")):
        with pytest.raises(ErroreControlloAggiornamenti):
            verifica_aggiornamento_disponibile("0.0.2")


def test_solleva_errore_se_risposta_senza_tag() -> None:
    with patch("urllib.request.urlopen", return_value=_risposta_finta({})):
        with pytest.raises(ErroreControlloAggiornamenti):
            verifica_aggiornamento_disponibile("0.0.2")


def test_confronto_versioni_ignora_prefisso_v_e_gestisce_lunghezze_diverse() -> None:
    with patch("urllib.request.urlopen", return_value=_risposta_finta({"tag_name": "v1.0"})):
        info = verifica_aggiornamento_disponibile("0.9.9")
    assert info.aggiornamento_disponibile is True
