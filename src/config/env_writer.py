"""
=====================================================================
 GRAVAÇÃO SEGURA DAS CHAVES (.env)
---------------------------------------------------------------------
 Salva/atualiza as chaves de API no arquivo .env (que fica só no
 computador do usuário). Usado pela tela de Configurações.
=====================================================================
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv, set_key

RAIZ = Path(__file__).resolve().parents[2]
ENV_PATH = RAIZ / ".env"


def salvar_valores(valores: dict[str, str]) -> None:
    """Grava cada chave no .env e recarrega para valer na hora."""
    if not ENV_PATH.exists():
        ENV_PATH.write_text("", encoding="utf-8")
    for chave, valor in valores.items():
        set_key(str(ENV_PATH), chave, valor or "", quote_mode="always")
    load_dotenv(ENV_PATH, override=True)
