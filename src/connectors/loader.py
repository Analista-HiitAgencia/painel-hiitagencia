"""
=====================================================================
 SELETOR DE CONECTOR
---------------------------------------------------------------------
 Decide, para cada rede, se usa o conector REAL (dados verdadeiros)
 ou o de DEMONSTRAÇÃO (dados simulados), conforme o arquivo .env.
=====================================================================
"""

from __future__ import annotations

from ..config.settings import esta_em_demo
from .base import ConectorBase
from .demo import ConectorDemo
from .deezer import ConectorDeezer
from .facebook import ConectorFacebook
from .instagram import ConectorInstagram
from .spotify import ConectorSpotify
from .vazio import ConectorVazio
from .youtube import ConectorYouTube

# Conectores REAIS já implementados (por rede).
_CONECTORES_REAIS = {
    "instagram": ConectorInstagram,
    "facebook": ConectorFacebook,
    "youtube": ConectorYouTube,
    "spotify": ConectorSpotify,
    "deezer": ConectorDeezer,
    # "tiktok":   ConectorTikTok,   # <- futuro
}


def obter_conector(rede_id: str) -> ConectorBase:
    """Devolve o conector adequado para a rede escolhida."""
    if esta_em_demo():
        return ConectorDemo(rede_id)

    classe = _CONECTORES_REAIS.get(rede_id)
    if classe is not None:
        return classe()

    # MODO REAL + rede ainda sem conector real: NÃO contribui (evita
    # misturar dado real com simulado). Fica de fora da soma.
    return ConectorVazio(rede_id)
