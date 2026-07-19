"""
=====================================================================
 CACHE DAS MÉTRICAS DO TIKTOK (guardado no banco)
---------------------------------------------------------------------
 Varrer os vídeos do TikTok tem custo (limite por minuto da API). Então
 guardamos o resultado (views e interações dos últimos 90 dias) no banco
 e só recalculamos 1x por dia — o painel lê o valor guardado na hora.
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
                artista TEXT PRIMARY KEY, views REAL, interacoes REAL, atualizado TEXT
            )"""
        ))
    # migração da tabela antiga (sem 'interacoes') em transação SEPARADA — no
    # Postgres um ALTER que falha aborta a transação inteira, então isola aqui.
    try:
        with engine().begin() as con:
            con.execute(text("ALTER TABLE tiktok_views ADD COLUMN interacoes REAL"))
    except Exception:  # noqa: BLE001 - coluna já existe: ok
        pass
    _CRIADA = True


def ler(artista: str) -> dict | None:
    _garantir_tabela()
    with engine().connect() as con:
        linha = con.execute(
            text("SELECT views, interacoes, atualizado FROM tiktok_views WHERE artista=:a"),
            {"a": artista},
        ).fetchone()
    if not linha:
        return None
    return {
        "views": float(linha[0] or 0),
        "interacoes": float(linha[1] or 0),
        "atualizado": linha[2],
    }


def salvar(artista: str, views: float, interacoes: float) -> None:
    _garantir_tabela()
    agora = datetime.utcnow().isoformat()
    with engine().begin() as con:
        con.execute(text("DELETE FROM tiktok_views WHERE artista=:a"), {"a": artista})
        con.execute(
            text("INSERT INTO tiktok_views (artista, views, interacoes, atualizado)"
                 " VALUES (:a, :v, :i, :t)"),
            {"a": artista, "v": float(views), "i": float(interacoes), "t": agora},
        )
