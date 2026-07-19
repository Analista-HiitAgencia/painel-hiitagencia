"""
=====================================================================
 CACHE DAS VISUALIZAÇÕES DO TIKTOK (guardado no banco)
---------------------------------------------------------------------
 Somar as views de TODOS os vídeos do TikTok é demorado (~40s numa
 conta com ~1.000 vídeos). Então guardamos o total no banco e só
 recalculamos 1x por dia — o painel lê o valor guardado na hora.
=====================================================================
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import text

from .db import engine

_CRIADA = False


def _garantir_tabela() -> None:
    global _CRIADA
    if _CRIADA:
        return
    with engine().begin() as con:
        con.execute(text(
            """CREATE TABLE IF NOT EXISTS tiktok_views (
                artista TEXT PRIMARY KEY, views REAL, atualizado TEXT
            )"""
        ))
    _CRIADA = True


def ler(artista: str) -> dict | None:
    _garantir_tabela()
    with engine().connect() as con:
        linha = con.execute(
            text("SELECT views, atualizado FROM tiktok_views WHERE artista=:a"),
            {"a": artista},
        ).fetchone()
    if not linha:
        return None
    return {"views": float(linha[0] or 0), "atualizado": linha[1]}


def salvar(artista: str, views: float) -> None:
    _garantir_tabela()
    agora = datetime.utcnow().isoformat()
    with engine().begin() as con:
        con.execute(text("DELETE FROM tiktok_views WHERE artista=:a"), {"a": artista})
        con.execute(
            text("INSERT INTO tiktok_views (artista, views, atualizado)"
                 " VALUES (:a, :v, :t)"),
            {"a": artista, "v": float(views), "t": agora},
        )
