"""
=====================================================================
 CONECTOR REAL DO INSTAGRAM  (Meta Graph API)  — visão mensal
---------------------------------------------------------------------
 Puxa dados VERDADEIROS da conta comercial do Instagram do artista.

 - Seguidores TOTAIS: sempre disponíveis.
 - Seguidores POR REGIÃO: usa a "audiência por cidade"
   (follower_demographics) e soma as cidades da mesorregião escolhida.
   Precisa da permissão instagram_manage_insights no token.
 - Alcance/Interações/Visualizações: números recentes da conta inteira
   (histórico por região se constrói acumulando leituras ao longo do
   tempo).
=====================================================================
"""

from __future__ import annotations

import unicodedata
from datetime import date, timedelta

import pandas as pd
import requests

from ..config.artists import dados_artista
from ..config.regions import nome_do_estado
from ..config.settings import get_env
from ..core.metrics import COLUNAS_METRICAS, JANELA_METRICAS_DIAS
from .base import ConectorBase

API_BASE = "https://graph.facebook.com/v20.0"


def _normalizar(texto: str) -> str:
    """Tira acentos, espaços e maiúsculas para casar nomes de cidade."""
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return t.strip().lower()


class ConectorInstagram(ConectorBase):
    rede_id = "instagram"

    def __init__(self) -> None:
        self.token = get_env("META_ACCESS_TOKEN")

    def _get(self, caminho: str, params: dict) -> dict:
        params = {**params, "access_token": self.token}
        resp = requests.get(f"{API_BASE}/{caminho}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _conta_id(self, artista_id: str) -> str:
        cfg = dados_artista(artista_id).get("redes", {}).get("instagram", {})
        return get_env(cfg.get("conta_id_env", ""))

    def _metrica_total(self, conta: str, metrica: str,
                       dias: int = JANELA_METRICAS_DIAS) -> float:
        """
        Total da métrica nos últimos `dias`. A API do Instagram limita cada
        consulta a 30 dias, então somamos em blocos de 30 até completar a janela.
        """
        total = 0.0
        achou = False
        fim = date.today()
        restante = dias
        while restante > 0:
            bloco = min(30, restante)
            since = fim - timedelta(days=bloco)
            try:
                dados = self._get(
                    f"{conta}/insights",
                    {"metric": metrica, "period": "day", "metric_type": "total_value",
                     "since": since.isoformat(), "until": fim.isoformat()},
                )
                for item in dados.get("data", []):
                    valor = (item.get("total_value") or {}).get("value")
                    if valor is not None:
                        total += float(valor)
                        achou = True
            except requests.HTTPError:
                pass
            fim = since
            restante -= bloco
        return total if achou else 0.0

    def _audiencia(self, conta: str, metrica: str,
                   timeframe: str | None = None) -> list[tuple[str, str, float]]:
        """
        Audiência por cidade -> lista de (cidade_norm, estado_norm, valor).
        `metrica`: follower_demographics / reached_audience_demographics /
        engaged_audience_demographics. `timeframe`: 'this_month' quando exigido.
        """
        params = {"metric": metrica, "period": "lifetime",
                  "metric_type": "total_value", "breakdown": "city"}
        if timeframe:
            params["timeframe"] = timeframe
        try:
            dados = self._get(f"{conta}/insights", params)
        except requests.HTTPError:
            return []
        registros: list[tuple[str, str, float]] = []
        for item in dados.get("data", []):
            for bd in (item.get("total_value") or {}).get("breakdowns", []):
                for res in bd.get("results", []):
                    nome = (res.get("dimension_values") or [""])[0]
                    partes = [p.strip() for p in nome.split(",")]
                    cidade = _normalizar(partes[0])
                    estado = _normalizar(partes[1]) if len(partes) > 1 else ""
                    registros.append((cidade, estado, float(res.get("value", 0))))
        return registros

    def _soma_regiao(self, registros: list[tuple[str, str, float]],
                     cidades: list[str], uf: str) -> float:
        """Soma o valor das cidades da região (casando cidade + estado)."""
        alvo = {_normalizar(c) for c in cidades}
        estado_nome = _normalizar(nome_do_estado(uf)) if uf else ""
        soma = 0.0
        for cidade, estado, valor in registros:
            if cidade not in alvo:
                continue
            if estado_nome and estado and estado_nome not in estado and estado not in estado_nome:
                continue  # cidade de mesmo nome, mas outro estado
            soma += valor
        return soma

    def serie_mensal(self, artista_id: str, cidades: list[str], meses: int,
                     uf: str = "") -> pd.DataFrame:
        conta = self._conta_id(artista_id)
        if not conta or not self.token:
            raise RuntimeError(
                "Sem credenciais do Instagram (META_ACCESS_TOKEN / ID da conta)."
            )

        if cidades:
            # ----- VISÃO REGIONAL (dados por cidade) -----
            # Seguidores: audiência atual por cidade.
            seguidores = self._soma_regiao(
                self._audiencia(conta, "follower_demographics"), cidades, uf)
            # Alcance/interações: por cidade, disponível só no mês atual.
            reach = self._audiencia(conta, "reached_audience_demographics", "this_month")
            eng = self._audiencia(conta, "engaged_audience_demographics", "this_month")
            alcance = self._soma_regiao(reach, cidades, uf)
            interacoes = self._soma_regiao(eng, cidades, uf)
            # Visualizações não têm dado por cidade: estima pela fatia de alcance
            # da região, usando as views do mês corrente (mesma janela do alcance).
            total_reach = sum(v for _, _, v in reach)
            dias_no_mes = max(1, date.today().day)
            views_mes = self._metrica_total(conta, "views", dias=dias_no_mes)
            visualizacoes = views_mes * (alcance / total_reach) if total_reach else 0.0
        else:
            # ----- CONTA INTEIRA (totais de 90 dias) -----
            info = self._get(conta, {"fields": "followers_count"})
            seguidores = float(info.get("followers_count", 0))
            alcance = self._metrica_total(conta, "reach")
            interacoes = (self._metrica_total(conta, "total_interactions")
                          or self._metrica_total(conta, "accounts_engaged"))
            visualizacoes = self._metrica_total(conta, "views")

        mes_atual = pd.Timestamp(date.today()).replace(day=1)
        df = pd.DataFrame([{
            "data": mes_atual,
            "seguidores": seguidores,
            "alcance": alcance,
            "interacoes": interacoes,
            "visualizacoes": visualizacoes,
        }])
        return df[["data"] + COLUNAS_METRICAS]
