"""
=====================================================================
 DADOS MANUAIS (streaming sem API — ex: Spotify streams/ouvintes)
---------------------------------------------------------------------
 O usuário digita à mão números que a API não libera (ex: streams e
 ouvintes do Spotify), e eles ficam salvos com data (cada atualização
 vira uma foto). Funciona local (SQLite) ou nuvem (Postgres) — ver db.py.
=====================================================================
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import text

from .db import engine

_CRIADA = False


def _garantir_tabela() -> None:
    global _CRIADA
    if _CRIADA:
        return
    with engine().begin() as con:
        con.execute(text(
            """CREATE TABLE IF NOT EXISTS spotify_manual (
                data TEXT, artista TEXT,
                seguidores REAL, streams REAL, ouvintes REAL,
                PRIMARY KEY (data, artista)
            )"""
        ))
    _CRIADA = True


def salvar_spotify(artista: str, seguidores: float, streams: float,
                   ouvintes: float) -> None:
    """Grava (ou atualiza) os números manuais do Spotify de hoje."""
    _garantir_tabela()
    hoje = date.today().isoformat()
    with engine().begin() as con:
        con.execute(
            text("DELETE FROM spotify_manual WHERE data=:d AND artista=:a"),
            {"d": hoje, "a": artista},
        )
        con.execute(
            text("""INSERT INTO spotify_manual
                 (data, artista, seguidores, streams, ouvintes)
                 VALUES (:d, :a, :s, :st, :o)"""),
            {"d": hoje, "a": artista, "s": float(seguidores or 0),
             "st": float(streams or 0), "o": float(ouvintes or 0)},
        )


def ler_spotify_atual(artista: str) -> dict | None:
    """Últimos números manuais do Spotify do artista (ou None se nunca preencheu)."""
    _garantir_tabela()
    with engine().connect() as con:
        row = con.execute(
            text("""SELECT seguidores, streams, ouvintes FROM spotify_manual
                 WHERE artista=:a ORDER BY data DESC LIMIT 1"""),
            {"a": artista},
        ).fetchone()
    if not row:
        return None
    return {"seguidores": row[0], "streams": row[1], "ouvintes": row[2]}
