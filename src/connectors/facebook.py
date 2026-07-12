"""
=====================================================================
 CONECTOR REAL DO FACEBOOK  (Meta Graph API — Página)
---------------------------------------------------------------------
 Usa o MESMO token da Meta. As métricas de Página exigem um "token da
 Página" — que este conector busca sozinho a partir de /me/accounts.
 Precisa do ID da Página (FB_PAGE_ID_BAILACO no .env).
=====================================================================
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import requests

from ..config.artists import dados_artista
from ..config.settings import get_env
from ..core.metrics import COLUNAS_METRICAS, JANELA_METRICAS_DIAS
from .base import ConectorBase

API_BASE = "https://graph.facebook.com/v20.0"


class ConectorFacebook(ConectorBase):
    rede_id = "facebook"

    def __init__(self) -> None:
        self.token = get_env("META_ACCESS_TOKEN")

    def _get(self, caminho: str, params: dict, token: str | None = None) -> dict:
        params = {**params, "access_token": token or self.token}
        resp = requests.get(f"{API_BASE}/{caminho}", params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _pagina_id(self, artista_id: str) -> str:
        cfg = dados_artista(artista_id).get("redes", {}).get("facebook", {})
        return get_env(cfg.get("pagina_id_env", ""))

    def _metrica_periodo(self, page: str, metrica: str, token: str,
                         dias: int = JANELA_METRICAS_DIAS) -> float:
        """Soma a métrica diária nos últimos `dias` (o Facebook aceita até 90)."""
        until = date.today()
        since = until - timedelta(days=min(dias, 90))
        try:
            dados = self._get(
                f"{page}/insights",
                {"metric": metrica, "period": "day",
                 "since": since.isoformat(), "until": until.isoformat()},
                token=token,
            )
        except requests.HTTPError:
            return 0.0
        soma = 0.0
        for item in dados.get("data", []):
            for v in item.get("values", []):
                valor = v.get("value")
                if isinstance(valor, (int, float)):
                    soma += valor
        return soma

    def serie_mensal(self, artista_id: str, cidades: list[str], meses: int,
                     uf: str = "") -> pd.DataFrame:
        # O Facebook não fornece seguidores por cidade. Por isso, quando uma
        # REGIÃO é escolhida, ele não entra na soma (evita inflar a região).
        # Só participa em "Conta inteira" (cidades vazio).
        if cidades:
            return pd.DataFrame(columns=["data"] + COLUNAS_METRICAS)

        page_id = self._pagina_id(artista_id)
        if not page_id or not self.token:
            raise RuntimeError("Sem ID da Página do Facebook / token.")

        # Busca a Página nas contas do usuário para pegar o TOKEN DA PÁGINA.
        contas = self._get(
            "me/accounts",
            {"fields": "id,name,access_token,followers_count,fan_count"},
        )
        pagina = next(
            (p for p in contas.get("data", []) if str(p.get("id")) == str(page_id)),
            None,
        )
        if not pagina:
            raise RuntimeError("Página não encontrada entre as suas contas.")

        page_token = pagina.get("access_token") or self.token
        seguidores = float(pagina.get("followers_count")
                           or pagina.get("fan_count") or 0)

        # Métricas de Página exigem a permissão read_insights. Muitas métricas
        # antigas foram aposentadas pela Meta; usamos as que ainda são válidas.
        interacoes = self._metrica_periodo(page_id, "page_post_engagements", page_token)
        visualizacoes = self._metrica_periodo(page_id, "page_views_total", page_token)
        alcance = 0.0  # sem métrica de alcance de Página válida na API atual

        mes_atual = pd.Timestamp(date.today()).replace(day=1)
        df = pd.DataFrame([{
            "data": mes_atual,
            "seguidores": seguidores,
            "alcance": alcance,
            "interacoes": interacoes,
            "visualizacoes": visualizacoes,
        }])
        return df[["data"] + COLUNAS_METRICAS]
