"""
=====================================================================
 CONECTOR BASE (modelo que todas as redes seguem)
---------------------------------------------------------------------
 Toda rede social implementa o mesmo "contrato": receber (artista,
 cidades, meses) e devolver uma tabela MENSAL com as métricas.
 Assim a ferramenta soma todas as redes de forma uniforme.
=====================================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class ConectorBase(ABC):
    """Contrato comum a todos os conectores de rede social."""

    rede_id: str = "base"

    @abstractmethod
    def serie_mensal(
        self,
        artista_id: str,
        cidades: list[str],
        meses: int,
        uf: str = "",
    ) -> pd.DataFrame:
        """
        Devolve um DataFrame MENSAL com as colunas:
            data | seguidores | alcance | interacoes | visualizacoes
        Uma linha por mês, já somando as `cidades` informadas.
        `uf` é a sigla do estado (usada para evitar cidades de mesmo
        nome em estados diferentes).
        """
        raise NotImplementedError
