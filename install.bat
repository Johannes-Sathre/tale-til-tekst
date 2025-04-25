@echo off
echo Tale til Tekst - Installasjonsscript
echo ==================================
echo.

REM Sjekk om Python er installert
python --version > NUL 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python er ikke installert eller ikke i PATH.
    echo Vennligst installer Python 3.9 eller 3.10 fra python.org
    echo og inkluder Python i PATH under installasjonen.
    pause
    exit /b 1
)

REM Opprett virtuelt miljø hvis det ikke eksisterer
if not exist venv\ (
    echo Oppretter virtuelt miljø...
    python -m venv venv
    if %ERRORLEVEL% NEQ 0 (
        echo Feil ved oppretting av virtuelt miljø.
        pause
        exit /b 1
    )
)

REM Aktiver virtuelt miljø og installer avhengigheter
echo Aktiverer virtuelt miljø og installerer avhengigheter...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo Feil ved installasjon av avhengigheter.
    pause
    exit /b 1
)

echo.
echo Installasjon fullført!
echo.
echo For å starte applikasjonen, kjør:
echo   start.bat
echo.
echo Første gang applikasjonen starter vil den laste ned Whisper-modellen (ca. 3GB).
echo.
pause 