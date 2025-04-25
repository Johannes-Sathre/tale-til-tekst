#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Hovedapplikasjon

En applikasjon som konverterer tale til tekst ved å bruke faster-whisper modellen.
"""

import os
import sys
import threading
import keyboard
import tkinter as tk
from tkinter import ttk

# Installer nødvendige avhengigheter hvis de mangler
def ensure_dependencies():
    """Sjekk om nødvendige pakker er installert, og installer dem hvis de mangler"""
    try:
        import PIL
    except ImportError:
        print("Installerer Pillow (PIL)...")
        os.system(f"{sys.executable} -m pip install pillow")

    try:
        import numpy
    except ImportError:
        print("Installerer numpy...")
        os.system(f"{sys.executable} -m pip install numpy")

    try:
        import pystray
    except ImportError:
        print("Installerer pystray...")
        os.system(f"{sys.executable} -m pip install pystray")

    try:
        import sounddevice
    except ImportError:
        print("Installerer sounddevice...")
        os.system(f"{sys.executable} -m pip install sounddevice")

    try:
        import pyperclip
    except ImportError:
        print("Installerer pyperclip...")
        os.system(f"{sys.executable} -m pip install pyperclip")

    try:
        import faster_whisper
    except ImportError:
        print("Installerer faster-whisper...")
        os.system(f"{sys.executable} -m pip install faster-whisper")

# Sikre at alle avhengigheter er installert
ensure_dependencies()

# Importer våre moduler
from gui import TaleApp
from recorder import setup_keyboard_hooks, cleanup
from transcriber import load_whisper_model

# Konfigurasjon
SHORTCUT = "ctrl+alt+s"  # Standard snarvei, kan endres

# Globale variabler
app = None

def main():
    """Hovedfunksjon som starter applikasjonen"""
    global app
    
    # Tilpass systemstiler
    if sys.platform == "win32":
        # Bruk moderne stil på Windows
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    
    # Opprett hovedvinduet
    root = tk.Tk()
    
    # Sentrer vinduet på skjermen
    window_width = 400
    window_height = 500
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width/2)
    center_y = int(screen_height/2 - window_height/2)
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    
    # Opprett TaleApp instansen
    app = TaleApp(root, SHORTCUT)
    
    # Last inn whisper-modellen i en bakgrunnstråd
    threading.Thread(target=lambda: load_whisper_model(app), daemon=True).start()
    
    # Registrer tastaturhendelser
    setup_keyboard_hooks(SHORTCUT, app)
    
    # Start hovedløkken
    root.mainloop()

if __name__ == "__main__":
    main() 