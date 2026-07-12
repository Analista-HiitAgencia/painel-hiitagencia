@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"
title HiitAgencia - Painel de Redes Sociais

echo ============================================================
echo   HiitAgencia - Painel de Redes Sociais
echo ============================================================
echo.

REM ---- 1) Localizar o Python (prioriza a instalacao real) ----
set "PY="
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY (
  where py >nul 2>nul && set "PY=py"
)
if not defined PY (
  echo [ERRO] Python nao encontrado. Instale o Python 3.12 e tente de novo.
  pause
  exit /b 1
)

REM ---- 2) Criar o ambiente isolado (.venv) na primeira vez ----
if not exist ".venv\Scripts\python.exe" (
  echo Preparando o ambiente pela primeira vez...
  "%PY%" -m venv .venv
)
call ".venv\Scripts\activate.bat"

REM ---- 3) Instalar os componentes (so na primeira vez) ----
if not exist ".venv\.instalado" (
  echo Instalando componentes. Isso pode levar alguns minutos na primeira vez...
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERRO] Falha ao instalar os componentes.
    pause
    exit /b 1
  )
  echo ok> ".venv\.instalado"
)

REM ---- 4) Evitar a pergunta de e-mail do Streamlit ----
if not exist "%USERPROFILE%\.streamlit" mkdir "%USERPROFILE%\.streamlit"
if not exist "%USERPROFILE%\.streamlit\credentials.toml" (
  >  "%USERPROFILE%\.streamlit\credentials.toml" echo [general]
  >> "%USERPROFILE%\.streamlit\credentials.toml" echo email = ""
)

echo.
echo Abrindo o painel em janela propria...
echo (Para FECHAR o painel, feche a janela do painel e depois esta janela preta.)
echo.
python launcher.py

pause
