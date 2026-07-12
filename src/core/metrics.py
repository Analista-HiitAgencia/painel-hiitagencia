"""
=====================================================================
 CÁLCULOS DE MÉTRICAS (visão macro / consolidada)
---------------------------------------------------------------------
 Os dados agora são MENSAIS e CONSOLIDADOS (somando todas as redes).
 Aqui ficam: os períodos, os nomes das métricas, o cálculo de
 crescimento (%) e a formatação dos números.
=====================================================================
"""

from __future__ import annotations

import pandas as pd

# As 4 métricas consolidadas que aparecem na tela (o "valor único").
METRICAS_CONSOLIDADAS: dict[str, dict] = {
    "seguidores":    {"rotulo": "Seguidores",    "icone": "👥"},
    "visualizacoes": {"rotulo": "Visualizações", "icone": "👁️"},
    "interacoes":    {"rotulo": "Interações",    "icone": "❤️"},
    "alcance":       {"rotulo": "Alcance",       "icone": "📡"},
}

COLUNAS_METRICAS = list(METRICAS_CONSOLIDADAS.keys())

# Janela de tempo (em dias) para alcance/interações/visualizações no modo real.
# 90 dias é o máximo prático (limite do Facebook; o Instagram é somado em
# blocos de 30 dias, que é o teto por consulta da API dele).
JANELA_METRICAS_DIAS = 90

# Períodos do filtro (rótulo -> nº de meses de janela).
PERIODOS: dict[str, int] = {
    "1 mês": 1,
    "3 meses": 3,
    "6 meses": 6,
    "1 ano": 12,
    "2 anos": 24,
    "5 anos": 60,
}


def crescimento(df: pd.DataFrame, coluna: str) -> dict:
    """
    Crescimento de uma métrica no período (dados mensais):
    compara o primeiro mês com o último mês do período.
    """
    if df.empty or coluna not in df:
        return {"inicio": 0.0, "fim": 0.0, "variacao": 0.0, "percentual": 0.0}

    serie = df.sort_values("data")[coluna].reset_index(drop=True)
    inicio = float(serie.iloc[0])
    fim = float(serie.iloc[-1])
    variacao = fim - inicio
    percentual = (variacao / inicio * 100.0) if inicio > 0 else 0.0
    return {"inicio": inicio, "fim": fim, "variacao": variacao, "percentual": percentual}


def valor_atual(df: pd.DataFrame, coluna: str) -> float:
    if df.empty or coluna not in df:
        return 0.0
    return float(df.sort_values("data")[coluna].iloc[-1])


def formatar_numero(valor: float) -> str:
    """1234567 -> '1.234.567' (padrão brasileiro, número cheio)."""
    return f"{int(round(valor)):,}".replace(",", ".")


def formatar_compacto(valor: float) -> str:
    """Versão curta para os cartões: 1.250.000 -> '1,3 mi' ; 540000 -> '540 mil'."""
    v = float(valor)
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f} mi".replace(".", ",")
    if v >= 1_000:
        return f"{v/1_000:.0f} mil"
    return formatar_numero(v)


def formatar_percentual(valor: float) -> str:
    sinal = "+" if valor >= 0 else ""
    return f"{sinal}{valor:.1f}%".replace(".", ",")
