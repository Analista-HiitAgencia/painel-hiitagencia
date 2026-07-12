"""
=====================================================================
 IDENTIDADE VISUAL (tema escuro + dourado da HiitAgência)
---------------------------------------------------------------------
 Aqui ficam o logotipo (em SVG) e o CSS que deixam o painel com a
 cara da marca — fundo escuro, acento dourado, cartões estilizados.
=====================================================================
"""

from __future__ import annotations

# Paleta da marca
OURO = "#E7BC91"
OURO_FORTE = "#E0A867"
FUNDO = "#141310"
CREME = "#F2EEE6"

# Símbolo da marca (recriado em SVG, escala perfeita em qualquer tamanho)
LOGO_SVG = (
    '<svg viewBox="0 0 110 72" width="44" height="44" '
    'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HiitAgência">'
    '<rect x="20" y="6"  width="13" height="60" rx="3" fill="#E7BC91"/>'
    '<rect x="77" y="6"  width="13" height="60" rx="3" fill="#E7BC91"/>'
    '<rect x="41" y="18" width="28" height="36" rx="3" fill="#E7BC91"/>'
    '<circle cx="55" cy="36" r="9" fill="#141310"/>'
    '<circle cx="55" cy="36" r="3.6" fill="#E7BC91"/>'
    "</svg>"
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp, [data-testid="stSidebar"] {
    font-family: 'Montserrat', -apple-system, sans-serif;
}

.stApp { background: radial-gradient(1200px 600px at 70% -10%, #1d1a12 0%, #141310 55%); }

/* Esconde a barra/menu padrão do Streamlit (cara de app) */
[data-testid="stToolbar"], #MainMenu, footer { display: none !important; }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.6rem; max-width: 1250px; }

/* Barra lateral */
[data-testid="stSidebar"] > div {
    background: #100F0B;
    border-right: 1px solid #2a2619;
}
[data-testid="stSidebar"] .hiit-logo-side { padding: 6px 4px 14px; border-bottom: 1px solid #2a2619; margin-bottom: 14px; }

/* Cabeçalho da marca */
.hiit-brand { display: flex; align-items: center; gap: 15px; margin: 2px 0 6px; }
.hiit-title { font-size: 30px; font-weight: 800; letter-spacing: 3px; color: #E7BC91; line-height: 1; }
.hiit-sub { font-size: 11.5px; color: #9c927e; letter-spacing: 2px; margin-top: 6px; text-transform: uppercase; }
.hiit-sub i { color: #E0A867; font-style: italic; }
.hiit-rule { height: 1px; background: linear-gradient(90deg, #E7BC91 0%, transparent 55%); margin: 10px 0 18px; }

/* Cartões de indicadores (KPIs) */
[data-testid="stMetric"] {
    background: linear-gradient(180deg, #201d15 0%, #1a1810 100%);
    border: 1px solid #322c1e;
    border-radius: 16px;
    padding: 18px 20px 14px;
    box-shadow: 0 6px 18px rgba(0,0,0,.25);
}
[data-testid="stMetricLabel"] p { color: #b3a893 !important; font-weight: 600; font-size: 13px; letter-spacing: .3px; }
[data-testid="stMetricValue"] { color: #E7BC91 !important; font-weight: 800; font-size: 34px; }

/* Botões (ex: baixar CSV) */
.stDownloadButton button, .stButton button {
    background: #E0A867; color: #1a1710; border: 0; border-radius: 10px;
    font-weight: 700; padding: 8px 18px;
}
.stDownloadButton button:hover, .stButton button:hover { background: #E7BC91; color: #16130d; }

/* Alertas (banner de demonstração) */
[data-testid="stAlert"] { background: #1C1A14; border: 1px solid #322c1e; border-left: 3px solid #E0A867; border-radius: 10px; }

/* Expander do detalhamento por rede */
[data-testid="stExpander"] { border: 1px solid #2a2619; border-radius: 12px; background: #17150f; }

/* Título de seções */
h3 { color: #F2EEE6; font-weight: 700; }
</style>
"""


def aplicar_tema(st) -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def cabecalho(st) -> None:
    st.markdown(
        '<div class="hiit-brand">' + LOGO_SVG +
        '<div><div class="hiit-title">HIITAGÊNCIA</div>'
        '<div class="hiit-sub">Painel de Redes Sociais · <i>conecta. cria. move.</i></div>'
        '</div></div><div class="hiit-rule"></div>',
        unsafe_allow_html=True,
    )


def logo_lateral(st) -> None:
    st.markdown(
        '<div class="hiit-logo-side" style="display:flex;align-items:center;gap:10px;">'
        + LOGO_SVG.replace('width="44" height="44"', 'width="30" height="30"')
        + '<span style="color:#E7BC91;font-weight:800;letter-spacing:2px;font-size:15px;">HIITAGÊNCIA</span></div>',
        unsafe_allow_html=True,
    )
