"""
=====================================================================
 BANCO DE DADOS (local ou nuvem)
---------------------------------------------------------------------
 Decide onde o histórico/dados manuais ficam guardados:
   - Se existir a variável DATABASE_URL (nuvem) -> banco Postgres (Neon).
   - Senão -> arquivo SQLite local (dados_locais/historico.db).

 O mesmo código funciona nos dois — só muda o "endereço" do banco.
=====================================================================
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

RAIZ = Path(__file__).resolve().parents[2]
_engine: Engine | None = None


def _url() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        # SQLAlchemy espera "postgresql://" (alguns serviços dão "postgres://").
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    # Sem DATABASE_URL: banco local em arquivo (SQLite).
    banco = RAIZ / "dados_locais" / "historico.db"
    banco.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{banco}"


def engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(_url(), pool_pre_ping=True, future=True)
    return _engine
