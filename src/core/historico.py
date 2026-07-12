"""
=====================================================================
 HISTÓRICO (fotos diárias para o crescimento ao longo do tempo)
---------------------------------------------------------------------
 Guarda uma "foto" por dia dos números de cada seleção (artista +
 região). Funciona local (SQLite) ou na nuvem (Postgres) — ver db.py.
 Assim o gráfico de evolução e o crescimento (%) se constroem no tempo.
=====================================================================
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from sqlalchemy import text

from .db import engine
from .metrics import COLUNAS_METRICAS

_CRIADA = False


def _garantir_tabela() -> None:
    global _CRIADA
    if _CRIADA:
        return
    with engine().begin() as con:
        con.execute(text(
            """CREATE TABLE IF NOT EXISTS fotos (
                data TEXT, artista TEXT, chave TEXT,
                seguidores REAL, alcance REAL, interacoes REAL, visualizacoes REAL,
                PRIMARY KEY (data, artista, chave)
            )"""
        ))
    _CRIADA = True


def registrar(artista: str, chave: str, metricas: dict) -> None:
    """Grava (ou atualiza) a foto de HOJE para uma seleção."""
    _garantir_tabela()
    hoje = date.today().isoformat()
    with engine().begin() as con:
        con.execute(
            text("DELETE FROM fotos WHERE data=:d AND artista=:a AND chave=:c"),
            {"d": hoje, "a": artista, "c": chave},
        )
        con.execute(
            text("""INSERT INTO fotos
                 (data, artista, chave, seguidores, alcance, interacoes, visualizacoes)
                 VALUES (:d, :a, :c, :s, :al, :i, :v)"""),
            {"d": hoje, "a": artista, "c": chave,
             "s": float(metricas.get("seguidores", 0)),
             "al": float(metricas.get("alcance", 0)),
             "i": float(metricas.get("interacoes", 0)),
             "v": float(metricas.get("visualizacoes", 0))},
        )


def ler(artista: str, chave: str, dias: int) -> pd.DataFrame:
    """Devolve o histórico (fotos) de uma seleção nos últimos `dias`."""
    _garantir_tabela()
    corte = (date.today() - timedelta(days=dias)).isoformat()
    with engine().connect() as con:
        linhas = con.execute(
            text("""SELECT data, seguidores, visualizacoes, interacoes, alcance
                 FROM fotos WHERE artista=:a AND chave=:c AND data>=:corte
                 ORDER BY data"""),
            {"a": artista, "c": chave, "corte": corte},
        ).fetchall()
    # A ordem das colunas do SELECT acima bate com ["data"] + COLUNAS_METRICAS
    # (seguidores, visualizacoes, interacoes, alcance) — não trocar!
    df = pd.DataFrame(linhas, columns=["data"] + COLUNAS_METRICAS)
    if not df.empty:
        df["data"] = pd.to_datetime(df["data"])
    return df
