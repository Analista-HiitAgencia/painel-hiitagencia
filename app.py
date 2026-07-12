"""
=====================================================================
 HiitAgência · Painel de Redes Sociais  (visão macro / consolidada)
---------------------------------------------------------------------
 O colaborador escolhe o ARTISTA, o ESTADO e a MESORREGIÃO. A tela
 mostra, num VALOR ÚNICO, a soma de TODAS as redes (Instagram,
 Facebook, YouTube e TikTok): seguidores, visualizações, interações
 e alcance — com o crescimento (%) no período.

 Para iniciar: dê 2 cliques no arquivo  INICIAR.bat
=====================================================================
"""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import nuvem, settings
from src.config.artists import REDES, cor_do_artista, listar_artistas
from src.config.regions import (
    CONTA_INTEIRA, cidades_da_mesorregiao, listar_estados,
    listar_mesorregioes, nome_da_mesorregiao,
)
from src.core import historico
from src.core.consolidado import serie_consolidada
from src.core.metrics import (
    COLUNAS_METRICAS, METRICAS_CONSOLIDADAS, PERIODOS, crescimento,
    formatar_compacto, formatar_numero, formatar_percentual, valor_atual,
)
from src.ui import acesso, configuracoes, tema

st.set_page_config(
    page_title=settings.APP_NOME,
    page_icon=settings.APP_ICONE,
    layout="wide",
)
tema.aplicar_tema(st)

# Na nuvem: carrega os segredos e exige senha. Local: passa direto.
nuvem.carregar_segredos_streamlit()
acesso.exigir_login(st)


@st.cache_data(ttl=900, show_spinner="Somando as redes da região...")
def carregar(artista: str, cidades: tuple, meses: int, modo: str, uf: str):
    # ttl=900: os dados se renovam sozinhos a cada 15 minutos.
    total, por_rede = serie_consolidada(artista, list(cidades), meses, uf)
    return total, por_rede


# ---------------------------------------------------------------------
#  Cabeçalho
# ---------------------------------------------------------------------
tema.cabecalho(st)

# ---------------------------------------------------------------------
#  Navegação (Painel x Configurações)
# ---------------------------------------------------------------------
tema.logo_lateral(st.sidebar)
pagina = st.sidebar.radio(
    "Navegação", ["📊 Painel", "⚙️ Configurações"], label_visibility="collapsed",
)

if pagina == "⚙️ Configurações":
    configuracoes.render(st)
    st.stop()

if settings.esta_em_demo():
    st.info(
        "🧪 **Modo demonstração** — números simulados, só para você ver a "
        "ferramenta funcionando. Para usar dados reais, abra **⚙️ Configurações** "
        "(menu à esquerda) e cole suas chaves de API.",
        icon="🧪",
    )
else:
    st.success("🔗 **Modo real** — dados obtidos das APIs oficiais.", icon="🔗")

# ---------------------------------------------------------------------
#  Barra lateral: filtros
# ---------------------------------------------------------------------
st.sidebar.header("🎛️ Filtros")

artistas = listar_artistas()
artista_id = st.sidebar.selectbox(
    "Artista", options=[a[0] for a in artistas],
    format_func=lambda x: dict(artistas)[x],
)

estados = listar_estados()
uf = st.sidebar.selectbox(
    "Estado", options=[e[0] for e in estados],
    format_func=lambda x: dict(estados)[x],
)

if uf == CONTA_INTEIRA:
    # Conta inteira: sem filtro de região (todas as redes, totais).
    cidades = ()
    uf_param = ""
    nome_regiao = "Conta inteira (todas as regiões)"
    chave_hist = "conta_inteira"
else:
    mesos = listar_mesorregioes(uf)
    meso_id = st.sidebar.selectbox(
        "Mesorregião", options=[m[0] for m in mesos],
        format_func=lambda x: dict(mesos)[x],
    )
    cidades = tuple(cidades_da_mesorregiao(uf, meso_id))
    uf_param = uf
    nome_regiao = nome_da_mesorregiao(uf, meso_id)
    chave_hist = f"{uf}:{meso_id}"

periodo_rotulo = st.sidebar.select_slider(
    "Período", options=list(PERIODOS.keys()), value="1 ano",
)
meses = PERIODOS[periodo_rotulo]

st.sidebar.divider()
if st.sidebar.button("🔄 Atualizar dados agora", use_container_width=True):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption(
    "Escolha **Conta inteira** para os totais de todas as redes, ou um "
    "**estado + mesorregião** (IBGE) para o público daquela região."
)

# ---------------------------------------------------------------------
#  Carregamento
# ---------------------------------------------------------------------
try:
    total, por_rede = carregar(artista_id, cidades, meses, settings.modo_dados(), uf_param)
except Exception as erro:  # noqa: BLE001
    st.error(f"❌ Erro ao obter os dados. Detalhe técnico: `{erro}`")
    st.stop()

if total.empty:
    st.warning("Nenhum dado encontrado para esta combinação de filtros.")
    st.stop()

# ---------------------------------------------------------------------
#  Histórico: grava a foto de hoje e monta a série de evolução
# ---------------------------------------------------------------------
if settings.esta_em_demo():
    serie_evolucao = total  # demo já tem série mensal simulada
else:
    valores_hoje = {m: valor_atual(total, m) for m in COLUNAS_METRICAS}
    historico.registrar(artista_id, chave_hist, valores_hoje)
    serie_evolucao = historico.ler(artista_id, chave_hist, meses * 31)
    if serie_evolucao.empty:
        serie_evolucao = total

# Contexto
nome_artista = dict(artistas)[artista_id]
redes_incluidas = " · ".join(
    f"{REDES[r]['icone']} {REDES[r]['nome']}" for r in por_rede
)
st.subheader(f"🎤 {nome_artista} — {nome_regiao}")
st.caption(f"Período: **{periodo_rotulo}**  ·  Redes somadas: {redes_incluidas}")

if not settings.esta_em_demo():
    if cidades:
        st.caption(
            "📍 **Região (dados por cidade):** Instagram (seguidores, alcance e "
            "interações do mês atual) + YouTube (visualizações reais, 90 dias). "
            "O Facebook não tem dado por cidade — aparece só em *Conta inteira*."
        )
    else:
        st.caption(
            "🌎 **Conta inteira:** alcance, interações e visualizações = "
            "totais dos **últimos 90 dias**."
        )

# ---------------------------------------------------------------------
#  Cartões consolidados (o "valor único")
# ---------------------------------------------------------------------
colunas = st.columns(len(METRICAS_CONSOLIDADAS))
for coluna, (chave, meta) in zip(colunas, METRICAS_CONSOLIDADAS.items()):
    calc = crescimento(serie_evolucao, chave)
    coluna.metric(
        label=f"{meta['icone']} {meta['rotulo']}",
        value=formatar_compacto(valor_atual(serie_evolucao, chave)),
        delta=f"{formatar_percentual(calc['percentual'])} no período",
    )

st.divider()

# ---------------------------------------------------------------------
#  Gráfico de evolução (mês a mês)
# ---------------------------------------------------------------------
st.markdown("### 📈 Evolução no período")

if serie_evolucao["data"].nunique() < 2:
    # Ainda sem histórico suficiente: só existe a "foto de hoje" (1 ponto).
    st.info(
        "📈 O gráfico de evolução aparece quando houver **fotos de mais de um "
        "dia**. A ferramenta já gravou a foto de hoje — cada vez que você usar, "
        "ela guarda mais uma, e em alguns dias a curva de crescimento aparece.",
        icon="⏳",
    )
else:
    metrica = st.selectbox(
        "Métrica do gráfico",
        options=list(METRICAS_CONSOLIDADAS.keys()),
        format_func=lambda x: METRICAS_CONSOLIDADAS[x]["rotulo"],
    )
    fig = px.area(serie_evolucao.sort_values("data"), x="data", y=metrica,
                  labels={"data": "Mês", metrica: METRICAS_CONSOLIDADAS[metrica]["rotulo"]})
    fig.update_traces(line_color="#E7BC91", fillcolor="rgba(231,188,145,0.18)",
                      line_width=2.5)
    fig.update_layout(
        margin=dict(l=0, r=0, t=10, b=0), height=380,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#B7AE9C",
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------
#  Detalhamento por rede (opcional, escondido num "expandir")
# ---------------------------------------------------------------------
with st.expander("🔎 Ver quanto cada rede contribui (detalhamento)"):
    linhas = []
    for rede_id, df_rede in por_rede.items():
        linha = {"Rede": f"{REDES[rede_id]['icone']} {REDES[rede_id]['nome']}"}
        for chave, meta in METRICAS_CONSOLIDADAS.items():
            linha[meta["rotulo"]] = formatar_numero(valor_atual(df_rede, chave))
        linhas.append(linha)
    if linhas:
        st.dataframe(pd.DataFrame(linhas), use_container_width=True, hide_index=True)
    if "youtube" in por_rede:
        st.caption(
            "ℹ️ YouTube = desempenho do **canal oficial** (uploads do canal). "
            "Não inclui as *Art Tracks* (faixas automáticas da distribuidora), "
            "que aparecem só no YouTube Studio."
        )
    if "spotify" in por_rede:
        st.caption(
            "ℹ️ Spotify (dados manuais): **Visualizações** = streams · "
            "**Alcance** = ouvintes (últimos 3 meses)."
        )

# ---------------------------------------------------------------------
#  Download
# ---------------------------------------------------------------------
exportar = serie_evolucao.sort_values("data").copy()
exportar["data"] = exportar["data"].dt.strftime("%d/%m/%Y")
st.download_button(
    "⬇️ Baixar histórico consolidado (CSV)",
    data=exportar.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"{artista_id}_{nome_regiao}_{periodo_rotulo}.csv".replace(" ", "_"),
    mime="text/csv",
)

st.divider()
st.caption(
    "HiitAgência · ferramenta interna de análise de redes sociais. "
    "Valores consolidados por mesorregião (IBGE), somando todas as redes."
)
