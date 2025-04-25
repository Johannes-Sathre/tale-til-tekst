#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Hovedapplikasjon

Startpunkt for applikasjonen som konverterer tale til tekst.
"""

import os
import sys
import threading

# Installer avhengigheter om nødvendig
def ensure_dependencies():
    """Sjekker og installerer nødvendige pakker"""
    packages = [
        "pillow",
        "numpy",
        "pystray",
        "sounddevice",
        "pyperclip",
        "faster-whisper",
        "keyboard",
        "cairosvg",
        "PyQt6",
        "qt-material"
    ]
    
    for package in packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            print(f"Installerer {package}...")
            os.system(f"{sys.executable} -m pip install {package}")

# Sikre at alle avhengigheter er installert
ensure_dependencies()

# Importer konfigurasjon
from config import SHORTCUT, setup_resources, configure_cpu_parameters

# Konfigurer CPU-parametre basert på systemet
configure_cpu_parameters()

# Oppsett av ressurser ved oppstart
setup_resources()

# Importer applikasjonsmoduler
from PyQt6.QtWidgets import QApplication
from modern_ui import ModernTaleApp
from recorder import Recorder
from transcriber import Transcriber

def main():
    """Hovedfunksjon"""
    # På Windows, håndter DPI-innstillinger
    if sys.platform == "win32":
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    # Opprett Qt-applikasjon
    qt_app = QApplication(sys.argv)
    
    # Opprett komponenter
    transcriber = Transcriber()
    recorder = Recorder(transcriber)
    
    # Opprett hovedapplikasjonen
    app = ModernTaleApp(SHORTCUT, recorder, transcriber)
    
    # Last inn Whisper-modellen i bakgrunnstråd
    threading.Thread(target=transcriber.load_model, daemon=True).start()
    
    # Sett opp tastaturlytting
    recorder.setup_keyboard_hooks(SHORTCUT)
    
    # Vis applikasjonen
    app.show()
    
    # Start hovedløkken
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    main() 