"""
=====================================================================
 CONECTOR DE DEMONSTRAÇÃO (dados mensais simulados)
---------------------------------------------------------------------
 Gera dados SIMULADOS (porém estáveis e realistas) para a ferramenta
 funcionar sem nenhuma chave de API. Cada rede tem um "perfil"
 diferente (ex: TikTok tem muitas visualizações; YouTube menos
 seguidores porém muitas views), para o total consolidado ficar crível.

 Os números NÃO são reais. Quando houver chaves e MODO_DADOS=real,
 o conector verdadeiro entra no lugar deste.
=====================================================================
"""

from __future__ import annotations

import hashlib
from datetime import date
from functools import lru_cache

import numpy as np
import pandas as pd

from ..core.metrics import COLUNAS_METRICAS
from .base import ConectorBase

# Linha do tempo: últimos 60 meses (5 anos), sempre terminando no mês atual.
_MESES = pd.date_range(
    end=pd.Timestamp(date.today()).replace(day=1), periods=60, freq="MS"
)
_N = len(_MESES)

# Perfil de cada rede: multiplicadores de seguidores / views / interações.
_PERFIL = {
    "instagram": {"seg": 1.0, "views": 1.2, "inter": 1.0},
    "tiktok":    {"seg": 0.8, "views": 3.2, "inter": 1.5},
    "youtube":   {"seg": 0.4, "views": 2.4, "inter": 0.6},
    "facebook":  {"seg": 0.6, "views": 0.7, "inter": 0.8},
}


def _semente(*partes: str) -> int:
    return int(hashlib.md5("::".join(partes).encode()).hexdigest()[:8], 16)


@lru_cache(maxsize=60000)
def _serie_cidade(artista_id: str, rede_id: str, cidade: str) -> tuple:
    """Série mensal (60 meses) de uma cidade numa rede. Fica em cache."""
    perf = _PERFIL.get(rede_id, _PERFIL["instagram"])
    rng = np.random.default_rng(_semente(artista_id, rede_id, cidade))

    base = rng.uniform(300, 3000) * perf["seg"]
    mult_5anos = rng.uniform(2.0, 6.0)
    taxa = np.clip(rng.normal(np.log(mult_5anos) / _N, 0.01, size=_N), -0.03, 0.15)
    seguidores = base * np.cumprod(1.0 + taxa)

    alcance = seguidores * rng.uniform(0.5, 1.2, size=_N) * (1 + rng.normal(0, 0.05, _N))
    interacoes = alcance * rng.uniform(0.05, 0.12) * perf["inter"] * (1 + rng.normal(0, 0.08, _N))
    visualizacoes = alcance * rng.uniform(0.8, 1.5) * perf["views"] * (1 + rng.normal(0, 0.10, _N))

    return (
        np.clip(seguidores, 0, None),
        np.clip(alcance, 0, None),
        np.clip(interacoes, 0, None),
        np.clip(visualizacoes, 0, None),
    )


class ConectorDemo(ConectorBase):
    def __init__(self, rede_id: str = "instagram") -> None:
        self.rede_id = rede_id

    def serie_mensal(self, artista_id: str, cidades: list[str], meses: int,
                     uf: str = "") -> pd.DataFrame:
        if not cidades:
            # "Conta inteira": usa todas as cidades cadastradas.
            from ..config.regions import todas_as_cidades
            cidades = todas_as_cidades()

        # Soma as séries de todas as cidades da região.
        soma = np.zeros((4, _N))
        for cidade in cidades:
            for i, arr in enumerate(_serie_cidade(artista_id, self.rede_id, cidade)):
                soma[i] += arr

        # Recorta o período pedido (últimos `meses`+1 pontos p/ ter início e fim).
        n = min(meses + 1, _N)
        datas = _MESES[-n:]
        recorte = soma[:, -n:]

        # Streaming (Spotify/Deezer) só tem seguidores/fãs — zera o resto.
        from ..config.artists import REDES_SO_SEGUIDORES
        so_seg = self.rede_id in REDES_SO_SEGUIDORES
        return pd.DataFrame({
            "data": datas,
            "seguidores": recorte[0].round(),
            "alcance": 0.0 if so_seg else recorte[1].round(),
            "interacoes": 0.0 if so_seg else recorte[2].round(),
            "visualizacoes": 0.0 if so_seg else recorte[3].round(),
        })
