"""
=====================================================================
 CONECTOR REAL DO SPOTIFY  (Web API)
---------------------------------------------------------------------
 Traz SEGUIDORES (e o índice de popularidade) do artista no Spotify.
 Usa o fluxo "Client Credentials": precisa de um Client ID e Client
 Secret (criados uma vez em developer.spotify.com) — NÃO precisa de
 login do artista. Também precisa do ID do artista no Spotify.

 Streaming não tem dado por cidade -> só entra em "Conta inteira".
 (Streams/ouvintes mensais não são liberados pela API pública.)
=====================================================================
"""

from __future__ import annotations

import base64
from datetime import date

import pandas as pd
import requests

from ..config.artists import dados_artista
from ..config.settings import get_env
from ..core.metrics import COLUNAS_METRICAS
from .base import ConectorBase

TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE = "https://api.spotify.com/v1"


class ConectorSpotify(ConectorBase):
    rede_id = "spotify"

    def __init__(self) -> None:
        self.client_id = get_env("SPOTIFY_CLIENT_ID")
        self.client_secret = get_env("SPOTIFY_CLIENT_SECRET")

    def _token(self) -> str:
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()).decode()
        r = requests.post(
            TOKEN_URL, data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth}"}, timeout=30)
        r.raise_for_status()
        return r.json()["access_token"]

    def _artista_id(self, artista_id: str) -> str:
        cfg = dados_artista(artista_id).get("redes", {}).get("spotify", {})
        return get_env(cfg.get("artista_id_env", ""))

    def serie_mensal(self, artista_id: str, cidades: list[str], meses: int,
                     uf: str = "") -> pd.DataFrame:
        if cidades:  # streaming não tem região
            return pd.DataFrame(columns=["data"] + COLUNAS_METRICAS)

        # O Spotify não libera streams/ouvintes pela API; usamos os dados
        # inseridos à mão (do painel Spotify for Artists).
        # Mapeamento: streams -> visualizações · ouvintes -> alcance.
        from ..core import manual
        dados = manual.ler_spotify_atual(artista_id)
        if not dados or not any(dados.values()):
            return pd.DataFrame(columns=["data"] + COLUNAS_METRICAS)

        mes_atual = pd.Timestamp(date.today()).replace(day=1)
        return pd.DataFrame([{
            "data": mes_atual,
            "seguidores": float(dados.get("seguidores", 0) or 0),
            "alcance": float(dados.get("ouvintes", 0) or 0),
            "interacoes": 0.0,
            "visualizacoes": float(dados.get("streams", 0) or 0),
        }])[["data"] + COLUNAS_METRICAS]
