"""
=====================================================================
 CONECTOR REAL DO TIKTOK  (Display API)
---------------------------------------------------------------------
 Traz, da conta autorizada de cada artista:
   - seguidores (follower_count)
   - interações  = total de curtidas da conta (likes_count)
   - visualizações = soma das views dos vídeos (video/list)
 O TikTok NÃO dá dado por cidade/região -> só entra em "Conta inteira"
 (igual ao Facebook e ao Spotify). Alcance não existe -> 0.

 Precisa do login por artista (ver tiktok_auth.py).
=====================================================================
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import requests

from ..core.metrics import COLUNAS_METRICAS
from . import tiktok_auth
from .base import ConectorBase

USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"
VIDEO_LIST_URL = "https://open.tiktokapis.com/v2/video/list/"
MAX_PAGINAS = 10  # até ~200 vídeos somados (20 por página)


class ConectorTikTok(ConectorBase):
    rede_id = "tiktok"

    def _headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def _user_info(self, token: str) -> tuple[float, float]:
        """Devolve (seguidores, curtidas_totais)."""
        r = requests.get(
            USER_INFO_URL,
            params={"fields": "follower_count,likes_count,video_count"},
            headers=self._headers(token), timeout=30,
        )
        r.raise_for_status()
        u = r.json().get("data", {}).get("user", {})
        return float(u.get("follower_count", 0) or 0), float(u.get("likes_count", 0) or 0)

    def _soma_views(self, token: str) -> float:
        """Soma as visualizações dos vídeos (paginado, com teto de segurança)."""
        total = 0.0
        cursor = None
        for _ in range(MAX_PAGINAS):
            corpo = {"max_count": 20}
            if cursor is not None:
                corpo["cursor"] = cursor
            r = requests.post(
                VIDEO_LIST_URL,
                params={"fields": "view_count"},
                json=corpo, headers=self._headers(token), timeout=30,
            )
            r.raise_for_status()
            dados = r.json().get("data", {})
            for v in dados.get("videos", []):
                total += float(v.get("view_count", 0) or 0)
            if not dados.get("has_more"):
                break
            cursor = dados.get("cursor")
        return total

    def serie_mensal(self, artista_id: str, cidades: list[str], meses: int,
                     uf: str = "") -> pd.DataFrame:
        vazio = pd.DataFrame(columns=["data"] + COLUNAS_METRICAS)
        if cidades:  # TikTok não tem dado por região
            return vazio

        token = tiktok_auth.obter_access_token(artista_id)
        if not token:
            return vazio  # sem autorização -> não contribui

        seguidores, curtidas = self._user_info(token)
        try:
            visualizacoes = self._soma_views(token)
        except Exception:  # noqa: BLE001 - sem permissão de vídeos: mantém 0
            visualizacoes = 0.0

        mes_atual = pd.Timestamp(date.today()).replace(day=1)
        return pd.DataFrame([{
            "data": mes_atual,
            "seguidores": seguidores,
            "alcance": 0.0,
            "interacoes": curtidas,
            "visualizacoes": visualizacoes,
        }])[["data"] + COLUNAS_METRICAS]
