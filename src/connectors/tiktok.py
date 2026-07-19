"""
=====================================================================
 CONECTOR REAL DO TIKTOK  (Display API)
---------------------------------------------------------------------
 Traz, da conta autorizada de cada artista:
   - seguidores (follower_count, valor atual)
   - visualizações = soma das views dos vídeos postados nos ÚLTIMOS 90 DIAS
   - interações    = soma de curtidas+comentários+compartilhamentos dos
                     vídeos dos últimos 90 dias
 A janela de 90 dias é a MESMA das outras redes (Instagram, YouTube,
 Facebook, Spotify) — para o consolidado ser coerente.

 O TikTok NÃO dá dado por cidade/região -> só entra em "Conta inteira".
 Alcance não existe no TikTok -> 0. Precisa do login por artista.
=====================================================================
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta

import pandas as pd
import requests

from ..core.metrics import COLUNAS_METRICAS, JANELA_METRICAS_DIAS
from . import tiktok_auth
from .base import ConectorBase

USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"
VIDEO_LIST_URL = "https://open.tiktokapis.com/v2/video/list/"
MAX_PAGINAS = 90       # teto de segurança de páginas (20 vídeos por página)
CACHE_HORAS = 20       # recalcula as métricas no máximo 1x por dia
PAUSA_PAGINA = 0.6     # pausa entre páginas p/ não estourar o limite por minuto
CAMPOS_VIDEO = "view_count,like_count,comment_count,share_count,create_time"


class ConectorTikTok(ConectorBase):
    rede_id = "tiktok"

    def _headers(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    def _follower_count(self, token: str) -> float:
        r = requests.get(
            USER_INFO_URL, params={"fields": "follower_count"},
            headers=self._headers(token), timeout=30,
        )
        r.raise_for_status()
        u = r.json().get("data", {}).get("user", {})
        return float(u.get("follower_count", 0) or 0)

    def _metricas_90d(self, token: str, artista_id: str) -> tuple[float, float]:
        """Views e interações dos vídeos dos últimos 90 dias. Cache diário.
        Devolve (visualizacoes, interacoes)."""
        cache = tiktok_cache_ler(artista_id)
        if cache and cache.get("atualizado"):
            try:
                idade = datetime.utcnow() - datetime.fromisoformat(cache["atualizado"])
                if idade < timedelta(hours=CACHE_HORAS):
                    return cache["views"], cache["interacoes"]  # valor recente guardado
            except Exception:  # noqa: BLE001
                pass

        corte = time.time() - JANELA_METRICAS_DIAS * 86400  # 90 dias atrás
        views = 0.0
        inter = 0.0
        cursor = None
        completo = False
        for _ in range(MAX_PAGINAS):
            corpo = {"max_count": 20}
            if cursor is not None:
                corpo["cursor"] = cursor
            try:
                r = requests.post(
                    VIDEO_LIST_URL, params={"fields": CAMPOS_VIDEO},
                    json=corpo, headers=self._headers(token), timeout=30,
                )
                r.raise_for_status()
                j = r.json()
            except Exception:  # noqa: BLE001 - erro/limite: para sem zerar o parcial
                break
            if (j.get("error") or {}).get("code") not in (None, "", "ok"):
                break
            dados = j.get("data", {})
            vids = dados.get("videos", [])
            recentes = 0
            for v in vids:
                ct = float(v.get("create_time", 0) or 0)
                if ct and ct < corte:
                    continue  # vídeo mais antigo que 90 dias -> fora da janela
                views += float(v.get("view_count", 0) or 0)
                inter += (float(v.get("like_count", 0) or 0)
                          + float(v.get("comment_count", 0) or 0)
                          + float(v.get("share_count", 0) or 0))
                recentes += 1
            if not dados.get("has_more") or not vids:
                completo = True
                break
            if recentes == 0:
                completo = True  # página inteira já passou dos 90 dias -> pode parar
                break
            cursor = dados.get("cursor")
            time.sleep(PAUSA_PAGINA)

        if completo:
            tiktok_cache_salvar(artista_id, views, inter)
            return views, inter
        # incompleto (ex.: rate limit): usa o último valor bom guardado, se houver
        if cache:
            return cache["views"], cache["interacoes"]
        return views, inter

    def serie_mensal(self, artista_id: str, cidades: list[str], meses: int,
                     uf: str = "") -> pd.DataFrame:
        vazio = pd.DataFrame(columns=["data"] + COLUNAS_METRICAS)
        if cidades:  # TikTok não tem dado por região
            return vazio

        token = tiktok_auth.obter_access_token(artista_id)
        if not token:
            return vazio  # sem autorização -> não contribui

        seguidores = self._follower_count(token)
        try:
            visualizacoes, interacoes = self._metricas_90d(token, artista_id)
        except Exception:  # noqa: BLE001 - sem permissão de vídeos: mantém 0
            visualizacoes, interacoes = 0.0, 0.0

        mes_atual = pd.Timestamp(date.today()).replace(day=1)
        return pd.DataFrame([{
            "data": mes_atual,
            "seguidores": seguidores,
            "alcance": 0.0,
            "interacoes": interacoes,
            "visualizacoes": visualizacoes,
        }])[["data"] + COLUNAS_METRICAS]


def tiktok_cache_ler(artista_id: str):
    from ..core import tiktok_cache
    return tiktok_cache.ler(artista_id)


def tiktok_cache_salvar(artista_id: str, views: float, interacoes: float) -> None:
    from ..core import tiktok_cache
    tiktok_cache.salvar(artista_id, views, interacoes)
