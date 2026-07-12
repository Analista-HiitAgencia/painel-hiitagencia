"""
=====================================================================
 CONECTOR REAL DO YOUTUBE  (YouTube Data API v3)
---------------------------------------------------------------------
 Versão inicial (com chave de API simples): traz os INSCRITOS do canal.
 As visualizações por período e dados por região exigem a API de
 Analytics (login OAuth) — ficam para uma etapa futura.

 Precisa de: YOUTUBE_API_KEY (compartilhada) e o ID do canal de cada
 artista (YOUTUBE_CHANNEL_ID_...), preenchidos na tela de Configurações.
 Como o YouTube não fornece dados por cidade, o canal só entra em
 "Conta inteira" (igual ao Facebook).
=====================================================================
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import requests

from ..config.artists import dados_artista
from ..config.settings import get_env
from ..core.metrics import COLUNAS_METRICAS, JANELA_METRICAS_DIAS
from . import youtube_auth
from .base import ConectorBase
from .instagram import _normalizar

API_BASE = "https://www.googleapis.com/youtube/v3"
ANALYTICS_BASE = "https://youtubeanalytics.googleapis.com/v2/reports"


class ConectorYouTube(ConectorBase):
    rede_id = "youtube"

    def __init__(self) -> None:
        self.key = get_env("YOUTUBE_API_KEY")

    def _canal_id(self, artista_id: str) -> str:
        cfg = dados_artista(artista_id).get("redes", {}).get("youtube", {})
        return get_env(cfg.get("canal_id_env", ""))

    def tem_acesso(self, artista_id: str) -> bool:
        """Verdadeiro se a conta autorizada REALMENTE acessa o canal deste artista."""
        try:
            canal = self._canal_id(artista_id)
            token = youtube_auth.obter_access_token(artista_id)
            if not (canal and token):
                return False
            self._analytics_periodo(canal, token)  # levanta erro se 403
            return True
        except Exception:  # noqa: BLE001
            return False

    def _analytics_periodo(self, canal: str, token: str,
                           dias: int = JANELA_METRICAS_DIAS) -> tuple[float, float]:
        """Views e interações (curtidas+comentários+compart.) nos últimos `dias`."""
        until = date.today()
        since = until - timedelta(days=dias)
        r = requests.get(
            ANALYTICS_BASE,
            params={"ids": f"channel=={canal}",
                    "startDate": since.isoformat(), "endDate": until.isoformat(),
                    "metrics": "views,likes,comments,shares"},
            headers={"Authorization": f"Bearer {token}"},
            timeout=30,
        )
        r.raise_for_status()
        linhas = r.json().get("rows", [])
        if not linhas:
            return 0.0, 0.0
        views, likes, comments, shares = (list(linhas[0]) + [0, 0, 0, 0])[:4]
        return float(views), float(likes) + float(comments) + float(shares)

    def _views_por_cidade(self, canal: str, artista_id: str) -> dict[str, float]:
        """Views por cidade nos últimos 90 dias -> {cidade_normalizada: views}."""
        token = youtube_auth.obter_access_token(artista_id)
        if not token:
            return {}
        until = date.today()
        since = until - timedelta(days=JANELA_METRICAS_DIAS)  # 90 dias (robusto)
        try:
            r = requests.get(
                ANALYTICS_BASE,
                params={"ids": f"channel=={canal}",
                        "startDate": since.isoformat(), "endDate": until.isoformat(),
                        "metrics": "views", "dimensions": "city",
                        "sort": "-views", "maxResults": 250},
                headers={"Authorization": f"Bearer {token}"}, timeout=30,
            )
            r.raise_for_status()
        except Exception:  # noqa: BLE001
            return {}
        resultado: dict[str, float] = {}
        for row in r.json().get("rows", []):
            cidade = _normalizar(str(row[0]))
            resultado[cidade] = resultado.get(cidade, 0.0) + float(row[1])
        return resultado

    def serie_mensal(self, artista_id: str, cidades: list[str], meses: int,
                     uf: str = "") -> pd.DataFrame:
        canal = self._canal_id(artista_id)
        if not canal or not self.key:
            raise RuntimeError("Sem chave de API / ID do canal do YouTube.")
        mes_atual = pd.Timestamp(date.today()).replace(day=1)
        vazio = pd.DataFrame(columns=["data"] + COLUNAS_METRICAS)

        # ----- VISÃO REGIONAL: só VIEWS por cidade (inscritos não têm cidade) -----
        if cidades:
            por_cidade = self._views_por_cidade(canal, artista_id)
            alvo = {_normalizar(c) for c in cidades}
            visualizacoes = sum(v for c, v in por_cidade.items() if c in alvo)
            if visualizacoes <= 0:
                return vazio  # sem views na região -> não contribui
            return pd.DataFrame([{
                "data": mes_atual, "seguidores": 0.0, "alcance": 0.0,
                "interacoes": 0.0, "visualizacoes": visualizacoes,
            }])[["data"] + COLUNAS_METRICAS]

        # ----- CONTA INTEIRA: inscritos + views/interações de 90 dias -----
        resp = requests.get(
            f"{API_BASE}/channels",
            params={"part": "statistics", "id": canal, "key": self.key},
            timeout=30,
        )
        resp.raise_for_status()
        itens = resp.json().get("items", [])
        if not itens:
            raise RuntimeError("Canal do YouTube não encontrado (confira o ID).")
        inscritos = float(itens[0].get("statistics", {}).get("subscriberCount", 0) or 0)

        visualizacoes = interacoes = 0.0
        try:
            token = youtube_auth.obter_access_token(artista_id)
            if token:
                visualizacoes, interacoes = self._analytics_periodo(canal, token)
        except Exception:  # noqa: BLE001 - sem analytics/acesso, mantém 0
            pass

        return pd.DataFrame([{
            "data": mes_atual,
            "seguidores": inscritos,
            "alcance": 0.0,
            "interacoes": interacoes,
            "visualizacoes": visualizacoes,
        }])[["data"] + COLUNAS_METRICAS]
