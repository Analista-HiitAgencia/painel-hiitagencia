"""
=====================================================================
 REGIÕES (base oficial do IBGE — mesorregiões)
---------------------------------------------------------------------
 A ferramenta usa a divisão oficial do IBGE. O usuário escolhe o
 ESTADO e a MESORREGIÃO; por trás, a ferramenta soma as cidades
 daquela mesorregião (o usuário não precisa ver por cidade).

 Os dados vêm do arquivo  dados/ibge_municipios.json  (gerado a partir
 da API do IBGE). A microrregião existe no arquivo, mas NÃO é exibida.
=====================================================================
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
_ARQUIVO = RAIZ / "dados" / "ibge_municipios.json"

# Ordem de exibição dos estados (Sul primeiro, como o Alex prefere).
_ORDEM_ESTADOS = ["RS", "SC", "PR", "MS", "MT", "GO", "SP", "MG"]

# Opção especial: somar todas as mesorregiões do estado.
TODO_O_ESTADO = "__estado__"

# Opção especial: conta inteira (sem filtro de região) — mostra os totais
# de todas as redes (inclusive Facebook, que não tem dado por cidade).
CONTA_INTEIRA = "__brasil__"


@lru_cache(maxsize=1)
def _base() -> dict:
    with open(_ARQUIVO, encoding="utf-8") as f:
        return json.load(f)["estados"]


def listar_estados() -> list[tuple[str, str]]:
    """[(sigla, 'RS — Rio Grande do Sul'), ...] com 'Conta inteira' no topo."""
    base = _base()
    itens = [(CONTA_INTEIRA, "🌎 Conta inteira (todas as regiões)")]
    siglas = [s for s in _ORDEM_ESTADOS if s in base]
    siglas += [s for s in sorted(base) if s not in siglas]
    for sigla in siglas:
        itens.append((sigla, f"{sigla} — {base[sigla]['nome']}"))
    return itens


def listar_mesorregioes(uf: str) -> list[tuple[str, str]]:
    """[(id, nome_exibicao), ...] já com a opção 'Todo o estado' no topo."""
    base = _base()
    est = base.get(uf, {})
    itens = [(TODO_O_ESTADO, f"🗺️ Todo o estado ({uf})")]
    for meso in est.get("mesorregioes", {}):
        itens.append((meso, meso))
    return itens


def cidades_da_mesorregiao(uf: str, meso: str) -> list[str]:
    """Todas as cidades da mesorregião (ou de todo o estado)."""
    base = _base()
    est = base.get(uf, {})
    mesos = est.get("mesorregioes", {})
    if meso == TODO_O_ESTADO:
        cidades: list[str] = []
        for micros in mesos.values():
            for lista in micros.values():
                cidades.extend(lista)
        return cidades
    cidades = []
    for lista in mesos.get(meso, {}).values():
        cidades.extend(lista)
    return cidades


def nome_da_mesorregiao(uf: str, meso: str) -> str:
    if meso == TODO_O_ESTADO:
        return f"Todo o estado ({uf})"
    return meso


def nome_do_estado(uf: str) -> str:
    """Nome completo do estado (ex: 'RS' -> 'Rio Grande do Sul')."""
    return _base().get(uf, {}).get("nome", uf)


def todas_as_cidades() -> list[str]:
    """Todas as cidades de todos os estados (usada no modo demo 'Conta inteira')."""
    cidades: list[str] = []
    for est in _base().values():
        for micros in est["mesorregioes"].values():
            for lista in micros.values():
                cidades.extend(lista)
    return cidades
