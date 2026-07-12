"""
=====================================================================
 CONTROLE DE ACESSO (login por senha)
---------------------------------------------------------------------
 Na nuvem, o painel fica protegido por uma senha (definida no segredo
 APP_PASSWORD). No uso local (sem APP_PASSWORD), o painel abre direto,
 sem pedir senha.
=====================================================================
"""

from __future__ import annotations

from ..config.settings import APP_ICONE, get_env


def exigir_login(st) -> None:
    senha_correta = get_env("APP_PASSWORD")
    if not senha_correta:
        return  # sem senha configurada (uso local) -> aberto
    if st.session_state.get("_acesso_ok"):
        return

    st.markdown(
        f"<div style='text-align:center;margin-top:8vh'>"
        f"<div style='font-size:40px'>{APP_ICONE}</div>"
        f"<h2 style='color:#E7BC91;letter-spacing:3px'>HIITAGÊNCIA</h2>"
        f"<p style='color:#9c927e'>Painel de Redes Sociais</p></div>",
        unsafe_allow_html=True,
    )
    col = st.columns([1, 2, 1])[1]
    with col:
        senha = st.text_input("Senha de acesso", type="password", key="_senha")
        if st.button("Entrar", type="primary", use_container_width=True):
            if senha == senha_correta:
                st.session_state["_acesso_ok"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    st.stop()
