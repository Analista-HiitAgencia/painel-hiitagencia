"""
=====================================================================
 SEGREDOS NA NUVEM
---------------------------------------------------------------------
 Quando hospedado no Streamlit Cloud, as chaves ficam guardadas nos
 "Secrets" da plataforma (st.secrets), não no arquivo .env. Aqui a
 gente copia esses segredos para as variáveis de ambiente, para o
 resto do código funcionar igual (local usa .env; nuvem usa secrets).
=====================================================================
"""

from __future__ import annotations

import os
from pathlib import Path


def _existe_arquivo_secrets() -> bool:
    """Só há secrets quando existe o arquivo (evita aviso feio no uso local)."""
    candidatos = [
        Path.cwd() / ".streamlit" / "secrets.toml",
        Path.home() / ".streamlit" / "secrets.toml",
    ]
    return any(p.exists() for p in candidatos)


def carregar_segredos_streamlit() -> None:
    """Copia st.secrets -> variáveis de ambiente (sem sobrescrever o .env local)."""
    if not _existe_arquivo_secrets():
        return  # uso local sem secrets -> nada a fazer
    try:
        import streamlit as st
        segredos = dict(st.secrets)
    except Exception:  # noqa: BLE001
        return
    for chave, valor in segredos.items():
        if isinstance(valor, (str, int, float, bool)):
            os.environ.setdefault(chave, str(valor))
