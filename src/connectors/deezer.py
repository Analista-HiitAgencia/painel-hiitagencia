"""
=====================================================================
 CONECTOR REAL DO DEEZER  (API pública)
---------------------------------------------------------------------
 Traz o número de FÃS (seguidores) do artista no Deezer. A API do
 Deezer é pública — não precisa de login/chave. Só do ID do artista
 (que a gente descobre pela busca).

 Streaming não tem dado por cidade -> só entra em "Conta inteira".
=====================================================================
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import requests

from ..config.artists import dados_artista
from ..config.settings import get_env
from ..core.metrics import COLUNAS_METRICAS
from .base import ConectorBase

API_BASE = "https://api.deezer.com"


class ConectorDeezer(ConectorBase):
    rede_id = "deezer"

    def _artista_id(self, artista_id: str) -> str:
        cfg = dados_artista(artista_id).get("redes", {}).get("deezer", {})
        return get_env(cfg.get("artista_id_env", ""))

    def serie_mensal(self, artista_id: str, cidades: list[str], meses: int,
                     uf: str = "") -> pd.DataFrame:
        if cidades:  # streaming não tem região
            return pd.DataFrame(columns=["data"] + COLUNAS_METRICAS)

        aid = self._artista_id(artista_id)
        if not aid:
            raise RuntimeError("Sem ID do artista no Deezer.")

        resp = requests.get(f"{API_BASE}/artist/{aid}", timeout=30)
        resp.raise_for_status()
        dados = resp.json()
        if dados.get("error"):
            raise RuntimeError("Artista não encontrado no Deezer (confira o ID).")

        fas = float(dados.get("nb_fan", 0) or 0)
        mes_atual = pd.Timestamp(date.today()).replace(day=1)
        return pd.DataFrame([{
            "data": mes_atual, "seguidores": fas,
            "alcance": 0.0, "interacoes": 0.0, "visualizacoes": 0.0,
        }])[["data"] + COLUNAS_METRICAS]
