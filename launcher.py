"""
=====================================================================
 INICIALIZADOR — abre o painel em JANELA PRÓPRIA (fora do navegador)
---------------------------------------------------------------------
 1) Sobe o servidor do painel (Streamlit) em segundo plano.
 2) Espera ele ficar pronto.
 3) Abre numa janela de aplicativo dedicada (sem barra do Chrome).
    Se a janela nativa não estiver disponível na máquina, abre
    automaticamente no navegador em "modo aplicativo" (também sem
    abas nem barra de endereço).

 Este arquivo é chamado pelo INICIAR.bat — você não precisa mexer nele.
=====================================================================
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PORTA = 8501
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORTA}"
TITULO = "HiitAgência · Painel de Redes Sociais"


def porta_ativa() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((HOST, PORTA)) == 0


def iniciar_servidor() -> subprocess.Popen | None:
    if porta_ativa():
        return None  # já está rodando
    # No Windows, evita abrir qualquer janela preta (console) do servidor.
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    return subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(RAIZ / "app.py"),
         "--server.port", str(PORTA), "--server.address", HOST,
         "--server.headless", "true"],
        cwd=str(RAIZ),
        creationflags=flags,
    )


def esperar_servidor(segundos: int = 60) -> bool:
    for _ in range(segundos * 2):
        if porta_ativa():
            return True
        time.sleep(0.5)
    return False


def abrir_modo_navegador() -> None:
    """Plano B: abre o navegador em modo aplicativo (janela limpa)."""
    candidatos = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    exe = next((c for c in candidatos if os.path.exists(c)), None)
    if exe:
        subprocess.Popen([exe, f"--app={URL}", "--window-size=1360,900"])
    else:
        import webbrowser
        webbrowser.open(URL)


def main() -> None:
    servidor = iniciar_servidor()
    print("Iniciando o painel, aguarde...")
    if not esperar_servidor():
        print("O servidor demorou a iniciar. Abrindo no navegador...")
        abrir_modo_navegador()
        if servidor:
            servidor.wait()
        return

    try:
        import webview  # janela nativa (pywebview)
        webview.create_window(TITULO, URL, width=1360, height=900,
                              min_size=(1024, 680))
        webview.start()  # bloqueia até o usuário fechar a janela
    except Exception as erro:  # noqa: BLE001
        print(f"Janela nativa indisponível ({erro}). Abrindo em modo aplicativo...")
        abrir_modo_navegador()
        if servidor:
            try:
                servidor.wait()
            except KeyboardInterrupt:
                pass
        return
    finally:
        if servidor:
            servidor.terminate()


if __name__ == "__main__":
    try:
        main()
    except Exception:  # noqa: BLE001 - sem console (pythonw): registra em arquivo
        import traceback
        (RAIZ / "launcher_erro.log").write_text(
            traceback.format_exc(), encoding="utf-8")
