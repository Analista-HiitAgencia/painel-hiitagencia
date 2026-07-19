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

import time
from datetime import date

import pandas as pd
import requests

from ..core.metrics import COLUNAS_METRICAS
from . import tiktok_auth
from .base import ConectorBase

USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"
VIDEO_LIST_URL = "https://open.tiktokapis.com/v2/video/list/"
MAX_PAGINAS = 90  # teto de segurança: até ~1800 vídeos somados (20 por página)
CACHE_HORAS = 20  # recalcula a soma de views no máximo 1x por dia
PAUSA_PAGINA = 0.6  # pausa entre páginas p/ não estourar o limite por minuto do TikTok


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

    def _soma_views(self, token: str, artista_id: str) -> float:
        """Soma as views de TODOS os vídeos. Guarda no banco e recalcula 1x/dia."""
        from datetime import datetime, timedelta

        from ..core import tiktok_cache
        cache = tiktok_cache.ler(artista_id)
        if cache and cache.get("atualizado"):
            try:
                idade = datetime.utcnow() - datetime.fromisoformat(cache["atualizado"])
                if idade < timedelta(hours=CACHE_HORAS):
                    return cache["views"]  # valor recente guardado -> instantâneo
            except Exception:  # noqa: BLE001
                pass

        total = 0.0
        cursor = None
        completo = False
        for _ in range(MAX_PAGINAS):
            corpo = {"max_count": 20}
            if cursor is not None:
                corpo["cursor"] = cursor
            try:
                r = requests.post(
                    VIDEO_LIST_URL,
                    params={"fields": "view_count"},
                    json=corpo, headers=self._headers(token), timeout=30,
                )
                r.raise_for_status()
                j = r.json()
            except Exception:  # noqa: BLE001 - erro/limite: para sem zerar o parcial
                break
            if (j.get("error") or {}).get("code") not in (None, "", "ok"):
                break  # rate limit / erro -> total ficou incompleto
            dados = j.get("data", {})
            vids = dados.get("videos", [])
            for v in vids:
                total += float(v.get("view_count", 0) or 0)
            if not dados.get("has_more"):
                completo = True
                break
            if not vids:
                break  # página vazia com has_more -> provável rate limit (incompleto)
            cursor = dados.get("cursor")
            time.sleep(PAUSA_PAGINA)  # respeita o limite por minuto do TikTok

        if completo and total > 0:
            tiktok_cache.salvar(artista_id, total)  # só guarda total confiável
            return total
        # incompleto (ex.: rate limit): usa o último valor bom guardado, se houver
        if cache and cache.get("views"):
            return cache["views"]
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
            visualizacoes = self._soma_views(token, artista_id)
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
