"""
=====================================================================
 AUTORIZAÇÃO DO TIKTOK (login OAuth)
---------------------------------------------------------------------
 Cuida do "login" com o TikTok que libera os dados da conta
 (seguidores, curtidas, visualizações dos vídeos).

 - montar_url_login(): monta o endereço para o dono da conta autorizar.
 - trocar_codigo(): troca o código recebido no retorno por um token
   (guarda o "refresh token" por artista).
 - obter_access_token(): usa o refresh token para renovar o acesso.

 Chaves (no .env / segredos):
   TIKTOK_CLIENT_KEY, TIKTOK_CLIENT_SECRET,
   TIKTOK_REFRESH_TOKEN_<ARTISTA>
=====================================================================
"""

from __future__ import annotations

from urllib.parse import urlencode

import requests

from ..config.settings import get_env
from ..core import tokens

AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
SCOPES = "user.info.stats,video.list"


def montar_url_login(redirect_uri: str, artista_id: str) -> str:
    """Endereço que o dono da conta abre para autorizar (usa `state` = artista)."""
    params = {
        "client_key": get_env("TIKTOK_CLIENT_KEY"),
        "scope": SCOPES,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "state": artista_id,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def trocar_codigo(codigo: str, redirect_uri: str, artista_id: str) -> str:
    """Troca o código do retorno por tokens e guarda o refresh token do artista."""
    r = requests.post(
        TOKEN_URL,
        data={
            "client_key": get_env("TIKTOK_CLIENT_KEY"),
            "client_secret": get_env("TIKTOK_CLIENT_SECRET"),
            "code": codigo,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    dados = r.json()
    refresh = dados.get("refresh_token", "")
    if refresh:
        tokens.salvar_token(artista_id, "tiktok", refresh)
    return refresh


def obter_access_token(artista_id: str) -> str | None:
    """Renova e devolve um access token. None se não autorizado."""
    rt = tokens.ler_token(artista_id, "tiktok")
    ck = get_env("TIKTOK_CLIENT_KEY")
    cs = get_env("TIKTOK_CLIENT_SECRET")
    if not (rt and ck and cs):
        return None
    r = requests.post(
        TOKEN_URL,
        data={
            "client_key": ck,
            "client_secret": cs,
            "grant_type": "refresh_token",
            "refresh_token": rt,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    r.raise_for_status()
    dados = r.json()
    # o TikTok pode devolver um refresh token novo — guarda o mais recente.
    novo_rt = dados.get("refresh_token")
    if novo_rt and novo_rt != rt:
        tokens.salvar_token(artista_id, "tiktok", novo_rt)
    return dados.get("access_token")


def esta_autorizado(artista_id: str) -> bool:
    return bool(tokens.ler_token(artista_id, "tiktok")
               and get_env("TIKTOK_CLIENT_KEY")
               and get_env("TIKTOK_CLIENT_SECRET"))
