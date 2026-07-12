"""
=====================================================================
 CONECTOR VAZIO
---------------------------------------------------------------------
 Usado no MODO REAL para redes que ainda NÃO têm conector verdadeiro
 (ex: TikTok antes de implementarmos). Ele devolve uma tabela vazia,
 ou seja, essa rede simplesmente NÃO entra na soma — evitando misturar
 número real com número simulado.
=====================================================================
"""

from __future__ import annotations

import pandas as pd

from ..core.metrics import COLUNAS_METRICAS
from .base import ConectorBase


class ConectorVazio(ConectorBase):
    def __init__(self, rede_id: str = "vazio") -> None:
        self.rede_id = rede_id

    def serie_mensal(self, artista_id: str, cidades: list[str], meses: int,
                     uf: str = "") -> pd.DataFrame:
        return pd.DataFrame(columns=["data"] + COLUNAS_METRICAS)
