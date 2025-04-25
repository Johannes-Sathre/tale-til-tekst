@echo off
setlocal

set PYTHON_VERSION=3.9

REM Tittel og introduksjon
title Tale til Tekst - Installasjon
echo ===================================================
echo       TALE TIL TEKST - INSTALLASJONSVERKTOY
echo ===================================================
echo.
echo Dette skriptet vil installere alle nodvendige komponenter
echo for Tale til Tekst-applikasjonen, inkludert virtuelle miljoer.
echo.
echo Systemkrav:
echo  - Windows 10/11
echo  - Python 3.9 eller nyere
echo  - Mikrofon
echo  - Minimum 8GB RAM for optimal ytelse
echo.
echo Vennligst sorge for at Python 3.9+ er installert for du fortsetter.
echo.
pause

REM Verifiser Python-installasjon
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [FEIL] Python ble ikke funnet. Vennligst installer Python 3.9 eller nyere.
    exit /b 1
)

REM Opprett virtuelt miljø hvis det ikke allerede eksisterer
if not exist venv\ (
    echo [INFO] Oppretter virtuelt Python-miljo...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo [FEIL] Kunne ikke opprette virtuelt miljo.
        exit /b 1
    )
)

REM Aktiver virtuelt miljø og installer pakker
echo [INFO] Aktiverer virtuelt miljo og installerer pakker...
call venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo [FEIL] Kunne ikke aktivere virtuelt miljo.
    exit /b 1
)

REM Installer avhengigheter
echo [INFO] Installerer pakker... Dette kan ta litt tid.
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [FEIL] Kunne ikke installere pakker.
    exit /b 1
)

echo.
echo [SUKSESS] Installasjonen er fullfort!
echo.
echo For a starte applikasjonen, kjor: start.bat
echo.
pause 