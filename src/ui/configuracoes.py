"""
=====================================================================
 TELA DE CONFIGURAÇÕES (chaves de API)
---------------------------------------------------------------------
 Onde o colaborador cola o token e o ID da conta, testa a conexão,
 estende a validade do token e liga o "modo real". Tudo salvo apenas
 no arquivo .env local — nada é enviado para fora.
=====================================================================
"""

from __future__ import annotations

import requests

from ..config import settings
from ..config.env_writer import ENV_PATH, salvar_valores

API_BASE = "https://graph.facebook.com/v20.0"


def _mascara(valor: str) -> str:
    if not valor:
        return "— (vazio)"
    if len(valor) <= 12:
        return valor[:2] + "…"
    return valor[:6] + "…" + valor[-4:]


def _probe_ig(token: str, node: str, metrica: str):
    from datetime import date, timedelta
    until = date.today()
    since = until - timedelta(days=28)
    try:
        r = requests.get(
            f"{API_BASE}/{node}/insights",
            params={"metric": metrica, "period": "day", "metric_type": "total_value",
                    "since": since.isoformat(), "until": until.isoformat(),
                    "access_token": token},
            timeout=20,
        )
        if r.status_code != 200:
            return f"erro {r.status_code}: {r.json().get('error', {}).get('message', '')[:90]}"
        for it in r.json().get("data", []):
            v = (it.get("total_value") or {}).get("value")
            if v is not None:
                return v
        return "sem dados"
    except Exception as e:  # noqa: BLE001
        return f"falha: {e}"


def _probe_fb(token: str, page: str, metrica: str):
    try:
        r = requests.get(
            f"{API_BASE}/{page}/insights",
            params={"metric": metrica, "period": "days_28", "access_token": token},
            timeout=20,
        )
        if r.status_code != 200:
            return f"erro {r.status_code}: {r.json().get('error', {}).get('message', '')[:90]}"
        for it in r.json().get("data", []):
            vals = it.get("values", [])
            if vals:
                return vals[-1].get("value")
        return "sem dados"
    except Exception as e:  # noqa: BLE001
        return f"falha: {e}"


def _probe_ig_cidades(token: str, ig_id: str):
    try:
        r = requests.get(
            f"{API_BASE}/{ig_id}/insights",
            params={"metric": "follower_demographics", "period": "lifetime",
                    "metric_type": "total_value", "breakdown": "city",
                    "access_token": token},
            timeout=20,
        )
        if r.status_code != 200:
            return f"erro {r.status_code}: {r.json().get('error', {}).get('message', '')[:90]}"
        cidades = []
        for it in r.json().get("data", []):
            for bd in (it.get("total_value") or {}).get("breakdowns", []):
                for res in bd.get("results", []):
                    nome = (res.get("dimension_values") or [""])[0]
                    cidades.append((res.get("value") or 0, nome))
        cidades.sort(reverse=True)
        return [f"{nome} → {val}" for val, nome in cidades[:12]] if cidades else "sem dados"
    except Exception as e:  # noqa: BLE001
        return f"falha: {e}"


def _probe_permissoes(token: str):
    try:
        r = requests.get(
            f"{API_BASE}/me/permissions", params={"access_token": token}, timeout=20
        )
        if r.status_code != 200:
            return f"erro {r.status_code}: {r.json().get('error', {}).get('message', '')[:90]}"
        data = r.json().get("data", [])
        concedidas = sorted(p["permission"] for p in data if p.get("status") == "granted")
        recusadas = sorted(p["permission"] for p in data if p.get("status") != "granted")
        return {"concedidas": concedidas, "recusadas": recusadas}
    except Exception as e:  # noqa: BLE001
        return f"falha: {e}"


def _diagnostico(st, token: str, ig_id: str, fb_page: str) -> None:
    if not token:
        st.error("Preencha/salve o token antes de diagnosticar.")
        return

    st.markdown("**🔑 Permissões que este token TEM:**")
    perms = _probe_permissoes(token)
    if isinstance(perms, dict):
        st.write("✅ Concedidas: " + (", ".join(perms["concedidas"]) or "—"))
        if perms["recusadas"]:
            st.write("⚠️ Recusadas/pendentes: " + ", ".join(perms["recusadas"]))
        if "instagram_manage_insights" in perms["concedidas"]:
            st.success("✅ `instagram_manage_insights` ESTÁ no token.")
        else:
            st.error(
                "❌ `instagram_manage_insights` NÃO está no token — "
                "é exatamente isso que falta!"
            )
    else:
        st.write(perms)

    st.markdown("**📷 Instagram:**")
    if ig_id:
        for m in ["reach", "total_interactions", "views", "impressions", "accounts_engaged"]:
            st.write(f"- `{m}` → `{_probe_ig(token, ig_id, m)}`")
        st.markdown("**🏙️ Instagram — audiência por cidade (usada na região):**")
        cidades_top = _probe_ig_cidades(token, ig_id)
        if isinstance(cidades_top, list):
            for linha in cidades_top:
                st.write(f"- {linha}")
        else:
            st.write(cidades_top)
    else:
        st.caption("_(sem ID do Instagram)_")
    st.markdown("**👍 Facebook:**")
    if fb_page:
        for m in ["page_impressions_unique", "page_post_engagements", "page_impressions"]:
            st.write(f"- `{m}` → `{_probe_fb(token, fb_page, m)}`")
    else:
        st.caption("_(sem ID da Página do Facebook)_")


def _testar_conexao(st, token: str, ig_id: str) -> None:
    if not token or not ig_id:
        st.error("Preencha o token e o ID da conta antes de testar.")
        return
    try:
        r = requests.get(
            f"{API_BASE}/{ig_id}",
            params={"fields": "username,followers_count", "access_token": token},
            timeout=25,
        )
        r.raise_for_status()
        d = r.json()
        st.success(
            f"✅ Conectado! Conta **@{d.get('username','?')}** — "
            f"**{d.get('followers_count','?')}** seguidores."
        )
    except Exception as erro:  # noqa: BLE001
        st.error(f"❌ Não conectou. Verifique o token/ID.\n\nDetalhe: `{erro}`")


def _estender_token(st, token: str, app_id: str, app_secret: str) -> None:
    if not (token and app_id and app_secret):
        st.error("Para estender, preencha token, App ID e App Secret.")
        return
    try:
        r = requests.get(
            f"{API_BASE}/oauth/access_token",
            params={
                "grant_type": "fb_exchange_token",
                "client_id": app_id,
                "client_secret": app_secret,
                "fb_exchange_token": token,
            },
            timeout=25,
        )
        r.raise_for_status()
        novo = r.json().get("access_token")
        if not novo:
            st.error("A Meta não devolveu um token estendido.")
            return
        salvar_valores({"META_ACCESS_TOKEN": novo, "META_APP_ID": app_id})
        st.success(
            "✅ Token estendido para ~60 dias e salvo! "
            "Agora ele não expira em poucas horas."
        )
    except Exception as erro:  # noqa: BLE001
        st.error(f"❌ Não deu para estender.\n\nDetalhe: `{erro}`")


def _envs_do_artista(art_id: str) -> dict[str, str]:
    """Nomes das variáveis (.env) de cada plataforma de um artista."""
    from ..config.artists import dados_artista
    redes = dados_artista(art_id).get("redes", {})
    return {
        "instagram": redes.get("instagram", {}).get("conta_id_env", ""),
        "facebook": redes.get("facebook", {}).get("pagina_id_env", ""),
        "youtube": redes.get("youtube", {}).get("canal_id_env", ""),
        "spotify": redes.get("spotify", {}).get("artista_id_env", ""),
        "deezer": redes.get("deezer", {}).get("artista_id_env", ""),
    }


def _diag_youtube(st) -> None:
    """Testa o login OAuth do YouTube AQUI (PC ou nuvem) e mostra o erro exato."""
    from ..config.artists import listar_artistas
    from ..connectors import youtube_auth
    from ..connectors.youtube import ConectorYouTube

    conn = ConectorYouTube()
    cid = settings.get_env("YOUTUBE_CLIENT_ID")
    cs = settings.get_env("YOUTUBE_CLIENT_SECRET")
    st.write(
        f"- Chave de API: {'✅' if settings.get_env('YOUTUBE_API_KEY') else '❌'}  ·  "
        f"Client ID: {'✅' if cid else '❌'}  ·  Client Secret: {'✅' if cs else '❌'}"
    )
    for a_id, a_nome in listar_artistas():
        rt = settings.get_env(youtube_auth._env_refresh(a_id))
        fim = ("…" + rt[-6:]) if rt else "— (VAZIO nesta máquina/nuvem)"
        st.markdown(f"**🎤 {a_nome}** — refresh token termina em `{fim}`")
        if not rt:
            st.error("Sem refresh token nas chaves. (Confira se a chave está nos Secrets.)")
            continue
        try:
            tok = youtube_auth.obter_access_token(a_id)
            if not tok:
                st.error("Não renovou o acesso (falta Client ID/Secret?).")
                continue
            views, inter = conn._analytics_periodo(conn._canal_id(a_id), tok)
            if views > 0:
                st.success(f"✅ Login OK — views(90d)={views:,.0f} · interações={inter:,.0f}")
            else:
                st.warning("Login renovou, mas veio views=0 (canal sem dados na janela?).")
        except Exception as e:  # noqa: BLE001
            st.error(f"❌ Falha ao renovar/consultar: `{type(e).__name__}: {str(e)[:180]}`")


def render(st) -> None:
    from ..config.artists import listar_artistas

    st.markdown("### ⚙️ Configurações — Chaves de API")
    st.caption(
        f"As chaves ficam salvas **só neste computador** (arquivo `{ENV_PATH.name}`) "
        "e nunca saem daqui. Nunca compartilhe esse arquivo."
    )

    token_atual = settings.get_env("META_ACCESS_TOKEN")
    appid_atual = settings.get_env("META_APP_ID")
    modo_atual = settings.modo_dados()
    artistas = listar_artistas()

    st.info(
        f"**Situação atual:**  Modo: **{modo_atual.upper()}**  ·  "
        f"Token da Meta: `{_mascara(token_atual)}`"
    )

    # ---- 1) Token (compartilhado por todos os artistas) ----
    st.markdown("#### 1) Token da Meta (vale para Instagram + Facebook de todos)")
    token = st.text_input(
        "Token de acesso da Meta", type="password", key="cfg_token",
        placeholder="cole aqui o token gerado no Explorador da API",
    )

    with st.expander("🔄 Estender validade do token para 60 dias (recomendado)"):
        st.caption(
            "O token do Explorador dura só ~1 hora. Com o App ID e o App Secret "
            "(em Configurações do app → Básico, no Meta for Developers), a gente "
            "estende para ~60 dias automaticamente."
        )
        app_id = st.text_input("App ID (ID do aplicativo)", value=appid_atual, key="cfg_appid")
        app_secret = st.text_input("App Secret (Chave secreta)", type="password", key="cfg_secret")
        if st.button("🔄 Estender e salvar token"):
            _estender_token(st, token or token_atual, app_id, app_secret)

    # ---- Chave do YouTube (compartilhada) ----
    yt_key = st.text_input(
        "Chave de API do YouTube (Google)", type="password", key="cfg_ytkey",
        value=settings.get_env("YOUTUBE_API_KEY"),
        placeholder="cole aqui a chave criada no Google Cloud",
    )

    with st.expander("▶️ YouTube — visualizações por período (login por artista)"):
        from ..connectors import youtube_auth
        from ..connectors.youtube import ConectorYouTube
        conector_yt = ConectorYouTube()
        st.caption(
            "Autorize o canal de **cada artista** com a conta Google que o "
            "administra (cada artista pode ter uma conta diferente). Precisa do "
            "**ID do cliente OAuth** e da **Chave secreta** (tipo *Desktop*)."
        )
        for a_id, a_nome in artistas:
            if conector_yt.tem_acesso(a_id):
                st.write(f"- 🎤 {a_nome}: ✅ conectado ao canal")
            else:
                st.write(f"- 🎤 {a_nome}: ⚠️ **não conectado** (autorize com a conta que administra o canal dele)")

        art_yt = st.selectbox(
            "Autorizar o canal de:", options=[a[0] for a in artistas],
            format_func=lambda x: dict(artistas)[x], key="cfg_yt_art",
        )
        st.caption(
            f"⚠️ No navegador, faça login com a conta que administra o canal do "
            f"**{dict(artistas)[art_yt]}** (confira o nome selecionado acima!)."
        )
        yt_cid = st.text_input("ID do cliente OAuth", key="cfg_yt_cid",
                               value=settings.get_env("YOUTUBE_CLIENT_ID"))
        yt_cs = st.text_input("Chave secreta do cliente OAuth", type="password",
                              key="cfg_yt_cs")
        if st.button("🔗 Conectar YouTube (abrir login no navegador)"):
            cid = yt_cid or settings.get_env("YOUTUBE_CLIENT_ID")
            cs = yt_cs or settings.get_env("YOUTUBE_CLIENT_SECRET")
            nome_art = dict(artistas)[art_yt]
            if not (cid and cs):
                st.error("Preencha o ID do cliente e a chave secreta primeiro.")
            else:
                with st.spinner("Abrindo o navegador... escolha a conta certa e aceite."):
                    try:
                        youtube_auth.autorizar(cid, cs, art_yt)
                        st.cache_data.clear()
                        if conector_yt.tem_acesso(art_yt):
                            st.success(f"✅ **{nome_art}** conectado ao canal! Recarregue o Painel.")
                        else:
                            st.error(
                                f"⚠️ Essa conta **não tem acesso** ao canal do "
                                f"**{nome_art}**. Clique de novo e escolha a conta "
                                f"que administra o canal dele."
                            )
                    except Exception as erro:  # noqa: BLE001
                        st.error(f"❌ Não deu para autorizar.\n\nDetalhe: `{erro}`")

    with st.expander("🔎 YouTube — diagnóstico (ver por que vem zero)"):
        st.caption(
            "Testa o login do YouTube **aqui** (no PC ou na nuvem) e mostra o "
            "erro exato — sem mostrar as chaves. Use para comparar PC × nuvem."
        )
        if st.button("🔎 Testar YouTube agora"):
            _diag_youtube(st)

    # ---- Credenciais do Spotify (compartilhadas) ----
    with st.expander("🟢 Spotify — credenciais (só uma vez, vale p/ todos)"):
        st.caption(
            "Crie um app grátis em **developer.spotify.com** (Dashboard → Create app) "
            "e cole aqui o **Client ID** e o **Client Secret**."
        )
        sp_cid = st.text_input("Spotify Client ID", key="cfg_sp_cid",
                               value=settings.get_env("SPOTIFY_CLIENT_ID"))
        sp_cs = st.text_input("Spotify Client Secret", type="password", key="cfg_sp_cs")

    # ---- Spotify: dados manuais (streams/ouvintes) ----
    with st.expander("📝 Spotify — atualizar streams/ouvintes (manual)"):
        from ..core import manual
        st.caption(
            "O Spotify não libera **streams** e **ouvintes** pela API. Preencha aqui "
            "com os números do painel **Spotify for Artists** (últimos 3 meses). "
            "Cada atualização vira uma foto no histórico."
        )
        art_sp = st.selectbox(
            "Artista", options=[a[0] for a in artistas],
            format_func=lambda x: dict(artistas)[x], key="cfg_spman_art",
        )
        atual_sp = manual.ler_spotify_atual(art_sp) or {}
        sp_seg = st.number_input(
            "Seguidores", min_value=0, step=100,
            value=int(atual_sp.get("seguidores", 0) or 0), key=f"cfg_spman_seg_{art_sp}")
        sp_str = st.number_input(
            "Streams (últimos 3 meses)", min_value=0, step=1000,
            value=int(atual_sp.get("streams", 0) or 0), key=f"cfg_spman_str_{art_sp}")
        sp_ouv = st.number_input(
            "Ouvintes (últimos 3 meses)", min_value=0, step=100,
            value=int(atual_sp.get("ouvintes", 0) or 0), key=f"cfg_spman_ouv_{art_sp}")
        if st.button(f"💾 Salvar dados do Spotify de {dict(artistas)[art_sp]}"):
            manual.salvar_spotify(art_sp, sp_seg, sp_str, sp_ouv)
            st.cache_data.clear()
            st.success("✅ Dados do Spotify salvos! Volte para o 📊 Painel.")

    # ---- 2) Contas de cada artista ----
    st.markdown("#### 2) Contas de cada artista")
    st.caption(
        "**IG** Instagram · **FB** Facebook · **YT** YouTube · "
        "**Spotify**/**Deezer** = ID do artista na plataforma."
    )
    ids_para_salvar: dict[str, str] = {}
    for art_id, art_nome in artistas:
        envs = _envs_do_artista(art_id)
        st.markdown(f"**🎤 {art_nome}**")
        c1, c2, c3 = st.columns(3)
        ig_val = c1.text_input("Instagram ID", value=settings.get_env(envs["instagram"]),
                               key=f"cfg_ig_{art_id}", placeholder="17841400000000000")
        fb_val = c2.text_input("Facebook Page ID", value=settings.get_env(envs["facebook"]),
                               key=f"cfg_fb_{art_id}", placeholder="1000000000000")
        yt_val = c3.text_input("YouTube — canal", value=settings.get_env(envs["youtube"]),
                               key=f"cfg_yt_{art_id}", placeholder="UCxxxxxxxx")
        c4, c5 = st.columns(2)
        sp_val = c4.text_input("Spotify — ID do artista", value=settings.get_env(envs["spotify"]),
                               key=f"cfg_sp_{art_id}", placeholder="ex: 6Mo...")
        dz_val = c5.text_input("Deezer — ID do artista", value=settings.get_env(envs["deezer"]),
                               key=f"cfg_dz_{art_id}", placeholder="ex: 15099331")
        for rede_chave, valor in [("instagram", ig_val), ("facebook", fb_val),
                                  ("youtube", yt_val), ("spotify", sp_val),
                                  ("deezer", dz_val)]:
            if envs[rede_chave]:
                ids_para_salvar[envs[rede_chave]] = valor

    # ---- 3) Diagnóstico (por artista) ----
    with st.expander("🔬 Diagnóstico das métricas (se algo vier zerado)"):
        st.caption("Mostra o que a Meta responde em cada métrica. Salve os IDs antes.")
        art_diag = st.selectbox(
            "Artista para diagnosticar", options=[a[0] for a in artistas],
            format_func=lambda x: dict(artistas)[x], key="cfg_diag_art",
        )
        envs_d = _envs_do_artista(art_diag)
        if st.button("🔬 Rodar diagnóstico"):
            _diagnostico(st, token or token_atual,
                         settings.get_env(envs_d["instagram"]),
                         settings.get_env(envs_d["facebook"]))

    # ---- 4) Ligar os dados reais ----
    st.markdown("#### 3) Ligar os dados reais")
    modo_real = st.toggle(
        "Usar dados reais agora (em vez da demonstração)",
        value=(modo_atual == "real"), key="cfg_real",
    )

    col1, col2 = st.columns(2)
    if col1.button("🧪 Testar conexão (1º artista)", use_container_width=True):
        primeiro = artistas[0][0]
        envs0 = _envs_do_artista(primeiro)
        _testar_conexao(st, token or token_atual, settings.get_env(envs0["instagram"]))

    if col2.button("💾 Salvar tudo", type="primary", use_container_width=True):
        valores = dict(ids_para_salvar)
        valores["MODO_DADOS"] = "real" if modo_real else "demo"
        if token:
            valores["META_ACCESS_TOKEN"] = token
        if yt_key:
            valores["YOUTUBE_API_KEY"] = yt_key
        if sp_cid:
            valores["SPOTIFY_CLIENT_ID"] = sp_cid
        if sp_cs:
            valores["SPOTIFY_CLIENT_SECRET"] = sp_cs
        salvar_valores(valores)
        st.cache_data.clear()
        st.success(
            "✅ Salvo! Volte para o **📊 Painel** (menu à esquerda) para ver os dados."
        )
