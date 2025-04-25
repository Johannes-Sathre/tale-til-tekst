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
    
    # Opprett hovedvinduet
    root = tk.Tk()
    
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