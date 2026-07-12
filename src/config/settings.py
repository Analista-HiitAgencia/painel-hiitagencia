"""
=====================================================================
 CONFIGURAÇÕES GERAIS
---------------------------------------------------------------------
 Lê o arquivo .env (as chaves de API) e decide se a ferramenta roda
 em modo DEMONSTRAÇÃO (dados simulados) ou REAL (dados verdadeiros).
=====================================================================
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega o arquivo .env que fica na raiz do projeto (se existir).
RAIZ = Path(__file__).resolve().parents[2]
load_dotenv(RAIZ / ".env")

# Identidade visual
APP_NOME = "HiitAgência · Painel de Redes Sociais"
APP_ICONE = "📊"


def modo_dados() -> str:
    """'demo' ou 'real'. Padrão: demo (seguro para testar)."""
    return os.getenv("MODO_DADOS", "demo").strip().lower()


def esta_em_demo() -> bool:
    return modo_dados() != "real"


def get_env(nome: str, padrao: str = "") -> str:
    return os.getenv(nome, padrao).strip()


def credenciais_meta_ok() -> bool:
    """Verdadeiro se há token da Meta configurado (Instagram/Facebook)."""
    return bool(get_env("META_ACCESS_TOKEN"))
