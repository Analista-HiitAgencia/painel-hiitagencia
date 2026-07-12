"""
=====================================================================
 AUTORIZAÇÃO DO YOUTUBE ANALYTICS (login OAuth)
---------------------------------------------------------------------
 Cuida do "login" único com o Google que libera as métricas de
 Analytics do YouTube (visualizações/curtidas/comentários por período).

 - autorizar(): abre o navegador para o dono do canal autorizar UMA vez.
   Guarda o "refresh token" no .env (não precisa logar de novo depois).
 - obter_access_token(): usa o refresh token para renovar o acesso
   automaticamente a cada uso.
=====================================================================
"""

from __future__ import annotations

from ..config.env_writer import salvar_valores
from ..config.settings import get_env

SCOPES = ["https://www.googleapis.com/auth/yt-analytics.readonly"]
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/auth"


def _config(client_id: str, client_secret: str) -> dict:
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": AUTH_URI,
            "token_uri": TOKEN_URI,
            "redirect_uris": ["http://localhost"],
        }
    }


def _env_refresh(artista_id: str | None) -> str:
    """Nome da variável do refresh token (por artista, ou compartilhado)."""
    if artista_id:
        return f"YOUTUBE_REFRESH_TOKEN_{artista_id.upper()}"
    return "YOUTUBE_REFRESH_TOKEN"


def _refresh_token(artista_id: str | None) -> str:
    """Refresh token específico do artista (cada canal é autorizado separado)."""
    return get_env(_env_refresh(artista_id))


def autorizar(client_id: str, client_secret: str,
              artista_id: str | None = None) -> str:
    """Abre o navegador para autorizar e salva o refresh token. Devolve-o.
    Se `artista_id` for dado, guarda o token específico daquele artista."""
    from google_auth_oauthlib.flow import InstalledAppFlow

    flow = InstalledAppFlow.from_client_config(_config(client_id, client_secret), SCOPES)
    # "select_account" força o Google a mostrar o seletor de contas, para o
    # usuário escolher a conta certa (a que administra ESTE canal).
    creds = flow.run_local_server(
        port=0, prompt="select_account consent", open_browser=True)
    salvar_valores({
        "YOUTUBE_CLIENT_ID": client_id,
        "YOUTUBE_CLIENT_SECRET": client_secret,
        _env_refresh(artista_id): creds.refresh_token or "",
    })
    return creds.refresh_token or ""


def esta_autorizado(artista_id: str | None = None) -> bool:
    return bool(_refresh_token(artista_id)
               and get_env("YOUTUBE_CLIENT_ID")
               and get_env("YOUTUBE_CLIENT_SECRET"))


def obter_access_token(artista_id: str | None = None) -> str | None:
    """Renova e devolve um access token. None se não autorizado."""
    rt = _refresh_token(artista_id)
    cid = get_env("YOUTUBE_CLIENT_ID")
    cs = get_env("YOUTUBE_CLIENT_SECRET")
    if not (rt and cid and cs):
        return None
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = Credentials(
        token=None, refresh_token=rt, client_id=cid, client_secret=cs,
        token_uri=TOKEN_URI, scopes=SCOPES,
    )
    creds.refresh(Request())
    return creds.token
