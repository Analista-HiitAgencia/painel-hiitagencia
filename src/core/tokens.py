"""
=====================================================================
 TOKENS OAUTH (guardados no banco, funciona local e na nuvem)
---------------------------------------------------------------------
 Alguns logins (ex.: TikTok) são feitos pela própria página do painel
 na nuvem. Como a nuvem não pode gravar no .env, o "refresh token"
 fica no banco (SQLite local ou Postgres/Neon na nuvem) — assim tanto
 o PC quanto a nuvem enxergam a mesma autorização.
=====================================================================
"""

from __future__ import annotations

from sqlalchemy import text

from .db import engine

_CRIADA = False


def _garantir_tabela() -> None:
    global _CRIADA
    if _CRIADA:
        return
    with engine().begin() as con:
        con.execute(text(
            """CREATE TABLE IF NOT EXISTS tokens_oauth (
                artista TEXT, rede TEXT, refresh_token TEXT,
                PRIMARY KEY (artista, rede)
            )"""
        ))
    _CRIADA = True


def salvar_token(artista: str, rede: str, refresh_token: str) -> None:
    _garantir_tabela()
    with engine().begin() as con:
        con.execute(
            text("DELETE FROM tokens_oauth WHERE artista=:a AND rede=:r"),
            {"a": artista, "r": rede},
        )
        con.execute(
            text("INSERT INTO tokens_oauth (artista, rede, refresh_token)"
                 " VALUES (:a, :r, :t)"),
            {"a": artista, "r": rede, "t": refresh_token},
        )


def ler_token(artista: str, rede: str) -> str:
    _garantir_tabela()
    with engine().connect() as con:
        linha = con.execute(
            text("SELECT refresh_token FROM tokens_oauth"
                 " WHERE artista=:a AND rede=:r"),
            {"a": artista, "r": rede},
        ).fetchone()
    return linha[0] if linha and linha[0] else ""
