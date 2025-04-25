#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Konfigurasjonsmodul

Inneholder globale konstanter og innstillinger for applikasjonen.
"""

import os
import multiprocessing

# Applikasjonsinformasjon
APP_VERSION = "1.1.0"
APP_NAME = "Tale til Tekst"

# OpenAI API-innstillinger
OPENAI_API_KEY = ""  # Tom standard, fylles ut av brukeren
OPENAI_MODEL = "gpt-3.5-turbo"  # Standard modell
OPENAI_CORRECTION_PROMPT = """Dette er en norsk transkripsjon. Korriger eventuelle ting du mistenker er feil, men behold meningen og ordene som er riktige. Svar kun med den korrigerte teksten, uten ekstra forklaringer."""

# Tastatursnarvei
SHORTCUT = "ctrl+alt+s"

# Lydinnstillinger
SAMPLE_RATE = 16000  # 16kHz
CHANNELS = 1  # Mono
SUPPORTED_RATES = [48000, 44100, 22050, 16000, 8000]  # Mulige sample rates i prioritert rekkefølge
TEST_DURATION = 3  # 3 sekunder mikrofontest

# Fargepalett - moderne og elegante farger
# Mørkt tema
DARK_BG = "#121212"           # Mørkere bakgrunn (hovedbakgrunn)
DARKER_BG = "#1E1E1E"         # Sekundær bakgrunn (for paneler)
DARKER_PANEL = "#262626"      # Mørkere panel bakgrunn
CARD_BG = "#2A2A2A"           # Bakgrunn for kort-elementer
ACCENT_COLOR = "#0A84FF"      # Blå aksentfarge
ACCENT_HOVER = "#60AFFF"      # Lysere aksentfarge for hover
TEXT_COLOR = "#FFFFFF"        # Lysere tekstfarge
SECONDARY_TEXT = "#AAAAAA"    # Sekundær tekstfarge
BORDER_COLOR = "#3A3A3A"      # Lysere borderfarge for kontrast
SUCCESS_COLOR = "#30D158"     # Grønn for suksess
WARNING_COLOR = "#FFD60A"     # Gul for advarsler
ERROR_COLOR = "#FF453A"       # Rød for feil
HEADER_BG = "#1A1A1A"         # Bakgrunnsfarge for topptekst
CARD_BORDER = "#3D3D3D"       # Kort-border
DIVIDER_COLOR = "#333333"     # Farge for delelinje

# Nye UI-elementer farger
SHADOW_COLOR = "rgba(0, 0, 0, 0.2)"  # Skyggeeffekt
OVERLAY_BG = "rgba(0, 0, 0, 0.7)"    # Overlay bakgrunn
ACTIVE_ITEM_BG = "#363636"           # Aktiv element bakgrunn
DISABLED_BG = "#252525"              # Deaktivert element bakgrunn
DISABLED_TEXT = "#6E6E6E"            # Deaktivert tekst
HIGHLIGHT_COLOR = "#4285F4"          # Uthevingsfarge
SECONDARY_ACCENT = "#9370DB"         # Sekundær aksentfarge
TERTIARY_ACCENT = "#00C7B7"          # Tertiær aksentfarge

# Lyse tema farger (for fremtidig implementasjon)
LIGHT_THEME = {
    "BG": "#F8F8F8",
    "DARKER_BG": "#EFEFEF",
    "PANEL_BG": "#FFFFFF",
    "CARD_BG": "#FFFFFF",
    "TEXT": "#212121",
    "SECONDARY_TEXT": "#616161",
    "ACCENT": "#0A84FF",
    "DIVIDER": "#E0E0E0"
}

# Fontinnstillinger
FONT_PRIMARY = "Segoe UI"
FONT_SECONDARY = "Roboto"
FONT_MONOSPACE = "Consolas"
FONT_SIZES = {
    "tiny": 8,
    "small": 10,
    "normal": 12,
    "medium": 14,
    "large": 16,
    "xlarge": 20,
    "title": 24
}

# Ressurser
def setup_resources():
    """Oppretter nødvendige ressursmapper hvis de ikke eksisterer"""
    resource_dirs = ["resources", "resources/icons", "resources/audio"]
    for directory in resource_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Opprettet mappe: {directory}")

# Whisper modellkonfigurasjon
AVAILABLE_WHISPER_MODELS = [
    "tiny", 
    "base", 
    "small", 
    "medium", 
    "large-v2", 
    "large-v3"
]
DEFAULT_WHISPER_MODEL = "medium"
WHISPER_MODEL = DEFAULT_WHISPER_MODEL  # Kan endres av brukeren
WHISPER_COMPUTE_TYPE = "int8"

# Dynamiske CPU-parametre som vil bli satt ved oppstart
WHISPER_CPU_THREADS = None  
WHISPER_NUM_WORKERS = None

def configure_cpu_parameters(model=None):
    """Konfigurerer CPU-parameterne basert på systemets ressurser og valgt modell"""
    global WHISPER_CPU_THREADS, WHISPER_NUM_WORKERS, WHISPER_MODEL
    
    # Oppdater modell hvis spesifisert
    if model and model in AVAILABLE_WHISPER_MODELS:
        WHISPER_MODEL = model
        print(f"Bruker Whisper-modell: {WHISPER_MODEL}")
    
    # Hent antall tilgjengelige CPU-kjerner
    cpu_count = multiprocessing.cpu_count()
    
    # Juster ressursbruk basert på modellstørrelse
    model_size_factor = 1.0
    if WHISPER_MODEL == "tiny" or WHISPER_MODEL == "base":
        model_size_factor = 0.5
    elif WHISPER_MODEL == "small":
        model_size_factor = 0.75
    elif WHISPER_MODEL == "large-v2" or WHISPER_MODEL == "large-v3":
        model_size_factor = 1.25
    
    # Konfigurerer tråder: Bruk justert prosent av tilgjengelige kjerner
    thread_percent = 0.75 * model_size_factor
    WHISPER_CPU_THREADS = max(2, min(int(cpu_count * thread_percent), 16))
    
    # Konfigurerer antall arbeidere basert på tilgjengelige kjerner og modellstørrelse
    if cpu_count <= 2:
        WHISPER_NUM_WORKERS = 1  # For svake systemer
    elif cpu_count <= 4:
        WHISPER_NUM_WORKERS = 2  # For middels systemer
    else:
        # For kraftige systemer, bruk justert prosent av kjernene
        worker_percent = 0.25 * model_size_factor
        WHISPER_NUM_WORKERS = max(2, min(int(cpu_count * worker_percent), 8))
    
    print(f"Systemkonfigurasjon: {cpu_count} CPU-kjerner oppdaget")
    print(f"Whisper CPU-tråder satt til: {WHISPER_CPU_THREADS}")
    print(f"Whisper arbeidere satt til: {WHISPER_NUM_WORKERS}")

def get_model_info():
    """Returnerer informasjon om tilgjengelige modeller og gjeldende valg"""
    return {
        "available_models": AVAILABLE_WHISPER_MODELS,
        "current_model": WHISPER_MODEL,
        "default_model": DEFAULT_WHISPER_MODEL
    }

# SVG-ikoner som brukes i applikasjonen
MICROPHONE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>"""

KEYBOARD_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect><path d="M6 8h.001"></path><path d="M10 8h.001"></path><path d="M14 8h.001"></path><path d="M18 8h.001"></path><path d="M8 12h.001"></path><path d="M12 12h.001"></path><path d="M16 12h.001"></path><path d="M7 16h10"></path></svg>"""

CLOSE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="34" height="34" viewBox="0 0 24 24">
  <line x1="6" y1="6" x2="18" y2="18" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" />
  <line x1="18" y1="6" x2="6" y2="18" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" />
</svg>"""

SETTINGS_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>"""