"""
=====================================================================
 ARTISTAS DO CASTING
---------------------------------------------------------------------
 Cadastro dos artistas e das redes sociais de cada um.

 >>> PARA ADICIONAR UM NOVO ARTISTA <<<
 Copie o bloco de um artista abaixo, troque o identificador (a chave),
 o "nome" e os dados de cada rede. Salve o arquivo. O artista já
 aparece no filtro da dashboard automaticamente.

 O campo "ativo" liga/desliga a rede sem precisar apagar nada.
 As variáveis tipo  env:META_ACCESS_TOKEN  são lidas do arquivo .env
 (onde ficam as chaves de API de verdade).
=====================================================================
"""

from __future__ import annotations

ARTISTAS: dict[str, dict] = {
    "bailaco": {
        "nome": "Bailaço",
        "cor": "#E63946",  # cor de destaque nos gráficos deste artista
        "redes": {
            "instagram": {
                "ativo": True,
                "usuario": "@bailaco",
                # ID da conta comercial do Instagram (vem do .env)
                "conta_id_env": "IG_BUSINESS_ID_BAILACO",
            },
            "facebook": {
                "ativo": True,
                "pagina_id_env": "FB_PAGE_ID_BAILACO",
            },
            "youtube": {
                "ativo": True,
                "canal_id_env": "YOUTUBE_CHANNEL_ID_BAILACO",
            },
            "tiktok": {
                "ativo": True,
                "conta_id_env": "TIKTOK_ACCOUNT_ID_BAILACO",
            },
            "spotify": {
                "ativo": True,
                "artista_id_env": "SPOTIFY_ARTIST_ID_BAILACO",
            },
            "deezer": {
                "ativo": True,
                "artista_id_env": "DEEZER_ARTIST_ID_BAILACO",
            },
        },
    },
    "primeira_dama": {
        "nome": "Primeira Dama",
        "cor": "#457B9D",
        "redes": {
            "instagram": {
                "ativo": True,
                "usuario": "@primeiradama",
                "conta_id_env": "IG_BUSINESS_ID_PRIMEIRA_DAMA",
            },
            "facebook": {"ativo": True, "pagina_id_env": "FB_PAGE_ID_PRIMEIRA_DAMA"},
            "youtube": {"ativo": True, "canal_id_env": "YOUTUBE_CHANNEL_ID_PRIMEIRA_DAMA"},
            "tiktok": {"ativo": True, "conta_id_env": "TIKTOK_ACCOUNT_ID_PRIMEIRA_DAMA"},
            "spotify": {"ativo": True, "artista_id_env": "SPOTIFY_ARTIST_ID_PRIMEIRA_DAMA"},
            "deezer": {"ativo": True, "artista_id_env": "DEEZER_ARTIST_ID_PRIMEIRA_DAMA"},
        },
    },
}

# Nome amigável e ícone de cada rede/plataforma.
REDES: dict[str, dict] = {
    "instagram": {"nome": "Instagram", "icone": "📷"},
    "facebook": {"nome": "Facebook", "icone": "👍"},
    "youtube": {"nome": "YouTube", "icone": "▶️"},
    "tiktok": {"nome": "TikTok", "icone": "🎵"},
    "spotify": {"nome": "Spotify", "icone": "🟢"},
    "deezer": {"nome": "Deezer", "icone": "🟣"},
}

# Plataformas que só têm "seguidores/fãs" no modo demonstração (o Deezer só dá
# fãs; o Spotify recebe streams/ouvintes manualmente, então não entra aqui).
REDES_SO_SEGUIDORES = {"deezer"}


def listar_artistas() -> list[tuple[str, str]]:
    """[(identificador, nome), ...]"""
    return [(ident, dados["nome"]) for ident, dados in ARTISTAS.items()]


def redes_ativas_do_artista(artista_id: str) -> list[tuple[str, str]]:
    """Redes ligadas de um artista: [(id_rede, nome_com_icone), ...]."""
    artista = ARTISTAS.get(artista_id, {})
    resultado = []
    for rede_id, cfg in artista.get("redes", {}).items():
        if cfg.get("ativo"):
            meta = REDES.get(rede_id, {"nome": rede_id, "icone": ""})
            resultado.append((rede_id, f"{meta['icone']} {meta['nome']}"))
    return resultado


def dados_artista(artista_id: str) -> dict:
    return ARTISTAS.get(artista_id, {})


def cor_do_artista(artista_id: str) -> str:
    return ARTISTAS.get(artista_id, {}).get("cor", "#E63946")
