"""
=====================================================================
 CONSOLIDAÇÃO (soma de todas as redes)
---------------------------------------------------------------------
 Pega TODAS as redes ativas do artista, busca a série mensal de cada
 uma e SOMA tudo num único conjunto de números — a visão que vai
 para o contratante. Também devolve o detalhamento por rede (para o
 "expandir" opcional na tela).
=====================================================================
"""

from __future__ import annotations

import pandas as pd

from ..config.artists import redes_ativas_do_artista
from ..connectors.loader import obter_conector
from .metrics import COLUNAS_METRICAS


def serie_consolidada(
    artista_id: str, cidades: list[str], meses: int, uf: str = ""
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """
    Devolve (total, por_rede):
      - total: DataFrame mensal somando todas as redes
      - por_rede: {rede_id: DataFrame mensal daquela rede}
    """
    total: pd.DataFrame | None = None
    por_rede: dict[str, pd.DataFrame] = {}

    for rede_id, _rotulo in redes_ativas_do_artista(artista_id):
        conector = obter_conector(rede_id)
        try:
            df = conector.serie_mensal(artista_id, list(cidades), meses, uf)
        except Exception:  # noqa: BLE001 - rede sem credencial/erro: ignora na soma
            continue
        if df is None or df.empty:
            continue

        por_rede[rede_id] = df
        if total is None:
            total = df.copy()
        else:
            total = (
                total.set_index("data")
                .add(df.set_index("data"), fill_value=0)
                .reset_index()
            )

    if total is None:
        total = pd.DataFrame(columns=["data"] + COLUNAS_METRICAS)

    return total.sort_values("data").reset_index(drop=True), por_rede
