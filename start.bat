@echo off
title Tale til Tekst
echo Starter Tale til Tekst...
echo.

REM Aktiver virtuelt miljø og start applikasjonen
call venv\Scripts\activate.bat
python app.py

echo.
pause 