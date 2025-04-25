#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - GUI-modul

Moderne brukergrensesnitt for Tale til Tekst-applikasjonen
"""

import os
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import numpy as np
import sounddevice as sd
import pystray
from PIL import Image, ImageTk
import keyboard
from cairosvg import svg2png
from io import BytesIO

def setup_resources():
    """Oppretter nødvendige ressursmapper hvis de ikke eksisterer"""
    resource_dirs = ["resources", "resources/icons", "resources/audio"]
    for directory in resource_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Opprettet mappe: {directory}")

# Opprett ressursmapper ved oppstart
setup_resources()

# Konstanter
SAMPLE_RATE = 16000  # 16kHz
CHANNELS = 1  # Mono
SUPPORTED_RATES = [48000, 44100, 22050, 16000, 8000]  # Mulige sample rates i prioritert rekkefølge

# Fargepalett
DARK_BG = "#1E1E1E"           # Mørkere bakgrunn
DARKER_BG = "#252526"         # Sekundær bakgrunn (for paneler)
ACCENT_COLOR = "#007ACC"      # Blå aksentfarge
ACCENT_HOVER = "#1C97EA"      # Lysere aksentfarge for hover
TEXT_COLOR = "#E8E8E8"        # Lysere tekstfarge
SECONDARY_TEXT = "#BBBBBB"    # Sekundær tekstfarge
BORDER_COLOR = "#3E3E3E"      # Lysere borderfarge for kontrast
SUCCESS_COLOR = "#3BB446"     # Grønn for suksess
WARNING_COLOR = "#DBAB09"     # Gul for advarsler
ERROR_COLOR = "#E51400"       # Rød for feil

def last_ikon(filnavn, størrelse=24):
    """Laster ikon fra SVG eller PNG-fil"""
    # Sjekk om filbanen er relativ
    if not os.path.isabs(filnavn):
        # Sjekk i resources/icons mappen
        if not filnavn.startswith("resources/"):
            ikon_fil = os.path.join("resources", "icons", filnavn)
        else:
            ikon_fil = filnavn
    else:
        ikon_fil = filnavn
        
    # Prøv å finne SVG-fil
    svg_fil = ikon_fil
    if not svg_fil.endswith(".svg"):
        svg_fil = f"{ikon_fil}.svg"
    
    # Prøv å finne PNG-fil
    png_fil = ikon_fil
    if not png_fil.endswith(".png"):
        png_fil = f"{ikon_fil}.png"
        
    try:
        # Først prøv SVG
        if os.path.exists(svg_fil):
            # Konverter SVG til PIL-image
            png_data = BytesIO()
            with open(svg_fil, 'rb') as svg_file:
                svg_data = svg_file.read()
                svg2png(bytestring=svg_data, write_to=png_data, 
                        output_width=størrelse, output_height=størrelse)
            png_data.seek(0)
            return ImageTk.PhotoImage(Image.open(png_data))
        
        # Så prøv PNG
        elif os.path.exists(png_fil):
            img = Image.open(png_fil)
            if img.width != størrelse or img.height != størrelse:
                img = img.resize((størrelse, størrelse), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
            
    except Exception as e:
        print(f"Feil ved lasting av ikon {filnavn}: {e}")
    
    return None

class ModernButton(tk.Frame):
    """Moderne knapp med ikon-støtte"""
    def __init__(self, parent, text, command=None, width=120, height=36):
        super().__init__(parent, width=width, height=height, bg=DARK_BG)
        self.pack_propagate(False)  # Behold angitt størrelse
        
        # Tilstand og funksjoner
        self.command = command
        self.width = width
        self.height = height
        self.text = text
        self.icon = None
        
        # Knappens bakgrunn
        self.canvas = tk.Canvas(self, bg=DARK_BG, highlightthickness=0, 
                               width=width, height=height)
        self.canvas.pack(fill="both", expand=True)
        
        # Tegn bakgrunn
        self.bg = self.canvas.create_rectangle(
            3, 3, width-3, height-3, fill=DARKER_BG, outline=BORDER_COLOR
        )
        
        # Legg til tekst
        self.text_x = width//2  # Standard tekstposisjon (midtstilt)
        self.text_obj = self.canvas.create_text(
            self.text_x, height//2, text=text, fill=TEXT_COLOR,
            font=("Segoe UI", 11), anchor="center"
        )
        
        # Bind hendelser
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
    
    def set_icon(self, icon):
        """Legg til et ikon på knappen"""
        self.icon = icon
        
        # Plasser ikon og tekst
        if icon:
            self.canvas.create_image(20, self.height//2, image=self.icon, anchor="w")
            self.text_x = 48  # Flytt tekst etter ikonet
            self.canvas.itemconfig(self.text_obj, anchor="w")
            self.canvas.coords(self.text_obj, self.text_x, self.height//2)
    
    def on_enter(self, event):
        self.canvas.itemconfig(self.bg, fill=ACCENT_COLOR)
        
    def on_leave(self, event):
        self.canvas.itemconfig(self.bg, fill=DARKER_BG)
        
    def on_click(self, event):
        self.canvas.itemconfig(self.bg, fill=ACCENT_HOVER)
        
    def on_release(self, event):
        self.canvas.itemconfig(self.bg, fill=ACCENT_COLOR)
        if self.command:
            self.command()

class RecordingIndicator(tk.Canvas):
    """Animert innspillingsindikator"""
    def __init__(self, parent, size=16):
        super().__init__(parent, width=size, height=size, bg=DARK_BG, 
                       highlightthickness=0)
        
        self.size = size
        self.is_active = False
        self.circle = self.create_oval(2, 2, size-2, size-2, 
                                    fill=ERROR_COLOR, outline="")
        self.pulse_size = 0
        self.pulse = self.create_oval(size/2, size/2, size/2, size/2, 
                                    fill="", outline=ERROR_COLOR)
        
    def start(self):
        """Start opptaksanimasjonen"""
        self.is_active = True
        self.pulse_animation()
        
    def stop(self):
        """Stopp opptaksanimasjonen"""
        self.is_active = False
        
    def pulse_animation(self):
        """Animer en pulserende ring rundt sirkelen"""
        if not self.is_active:
            self.delete(self.pulse)
            self.pulse = self.create_oval(self.size/2, self.size/2, 
                                       self.size/2, self.size/2, 
                                       fill="", outline=ERROR_COLOR)
            return
            
        # Øk størrelsen på pulseringen
        self.pulse_size = (self.pulse_size + 1) % 20
        size = self.size * (0.5 + self.pulse_size/40)
        x1 = (self.size - size) / 2
        y1 = (self.size - size) / 2
        x2 = x1 + size
        y2 = y1 + size
        
        # Oppdater pulseringen
        self.delete(self.pulse)
        alpha = 50 - self.pulse_size * 2.5
        if alpha < 0: alpha = 0
        color = f"#{ERROR_COLOR[1:]}{'%02x' % int(alpha)}"
        self.pulse = self.create_oval(x1, y1, x2, y2, 
                                   fill="", outline=color, width=2)
        
        # Fortsett animasjonen
        self.after(50, self.pulse_animation)

class TaleApp:
    def __init__(self, root, shortcut):
        self.root = root
        self.shortcut = shortcut
        self.setup_gui()
        self.is_recording = False
        self.transcription_count = 0
        self.selected_device = 0  # Standard mikrofon
        self.device_sample_rate = 16000  # Standard sample rate
        self.is_transcribing = False  # For å spore transkripsjonsstatus
        
        # System tray-variabler
        self.tray_icon = None
        self.minimized_to_tray = False
        
        # Oppdater mikrofoner ved oppstart
        self.update_microphones()
        
        # Oppsett av system tray
        self.setup_tray()
        
        # Håndter lukkeknappen (X)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Plasser vinduet over system tray (nederst til høyre)
        self.position_window_at_tray()
        
    def setup_gui(self):
        """Sett opp brukergrensesnittet"""
        self.root.title("Tale til Tekst")
        self.root.geometry("600x900")
        self.root.minsize(600, 900)
        
        # Fjern standard tittellinjen
        self.root.overrideredirect(True)
        
        # Gjør vinduet flyttbart med musen
        self.make_window_movable()
        
        # Prøv å laste app-ikon
        try:
            app_icon = last_ikon("app_icon", 32)
            if app_icon:
                self.root.iconphoto(True, app_icon)
        except Exception as e:
            print(f"Kunne ikke sette ikon: {e}")
        
        # Stil for ttk-komponenter
        style = ttk.Style()
        style.configure('Dark.TFrame', background=DARK_BG)
        style.configure('Dark.TLabel', background=DARK_BG, foreground=TEXT_COLOR)
        style.configure('Dark.TButton', background=DARK_BG, foreground=TEXT_COLOR)
        
        # Konfigurerer layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Hovedramme
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Konfigurer main_frame til å være responsiv
        for i in range(1):
            main_frame.grid_columnconfigure(i, weight=1)
            
        main_frame.grid_rowconfigure(0, weight=0)  # Tittel
        main_frame.grid_rowconfigure(1, weight=0)  # Status
        main_frame.grid_rowconfigure(2, weight=0)  # Knapper
        main_frame.grid_rowconfigure(3, weight=0)  # Mikrofon
        main_frame.grid_rowconfigure(4, weight=1)  # Transkripsjon
        main_frame.grid_rowconfigure(5, weight=1)  # Logg
        
        # Toppramme med tittel og lukkeknapp
        top_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ttk.Label(top_frame, text="Tale til Tekst", style='Dark.TLabel', font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # Lukke-knapp
        close_button = ttk.Button(top_frame, text="X", command=self.on_close, width=3)
        close_button.grid(row=0, column=1, sticky="e")
        
        # Status-panel
        status_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        status_frame.grid(row=1, column=0, sticky="ew", pady=5)
        status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="Laster modell...")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, 
                                    style='Dark.TLabel', font=("Arial", 12))
        self.status_label.grid(row=0, column=0, sticky="w")
        
        # Modellstatus
        self.model_status_var = tk.StringVar(value="Modellstatus: Laster...")
        self.model_status = ttk.Label(status_frame, textvariable=self.model_status_var, 
                                   font=("Arial", 10), foreground=WARNING_COLOR, background=DARK_BG)
        self.model_status.grid(row=0, column=1, sticky="e")
        
        # Modus-knapper
        modes_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        modes_frame.grid(row=2, column=0, sticky="ew", pady=10)
        modes_frame.grid_columnconfigure(0, weight=1)
        modes_frame.grid_columnconfigure(1, weight=1)
        
        # Last ikoner til knappene
        mic_icon = last_ikon("microphone", 24)
        settings_icon = last_ikon("settings", 24)
        
        # Knapper i moderne stil
        self.mic_button = ModernButton(modes_frame, "Test mikrofon", self.test_microphone, width=280, height=40)
        if mic_icon:
            self.mic_button.set_icon(mic_icon)
        self.mic_button.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.settings_button = ModernButton(modes_frame, "Innstillinger", self.show_settings, width=280, height=40)
        if settings_icon:
            self.settings_button.set_icon(settings_icon)
        self.settings_button.grid(row=0, column=1, sticky="e")
        
        # Mikrofon-valgpanel og gain i samme ramme
        controls_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        controls_frame.grid(row=3, column=0, sticky="ew", pady=10)
        controls_frame.grid_columnconfigure(0, weight=0)
        controls_frame.grid_columnconfigure(1, weight=1)
        controls_frame.grid_columnconfigure(2, weight=0)
        
        # Mikrofon
        ttk.Label(controls_frame, text="Mikrofon:", style='Dark.TLabel', font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        self.mic_var = tk.StringVar()
        self.mic_dropdown = ttk.Combobox(controls_frame, textvariable=self.mic_var, width=50, state="readonly", font=("Arial", 10))
        self.mic_dropdown.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Følsomhet (gain)
        ttk.Label(controls_frame, text="Følsomhet:", style='Dark.TLabel', font=("Arial", 11)).grid(row=1, column=0, sticky="w", padx=(0, 5), pady=(10, 0))
        
        gain_frame = ttk.Frame(controls_frame, style='Dark.TFrame')
        gain_frame.grid(row=1, column=1, sticky="ew", pady=(10, 0))
        gain_frame.grid_columnconfigure(0, weight=1)
        
        self.gain_var = tk.DoubleVar(value=1.0)
        self.gain_scale = ttk.Scale(gain_frame, from_=0.1, to=5.0, 
                                 orient=tk.HORIZONTAL, variable=self.gain_var)
        self.gain_scale.grid(row=0, column=0, sticky="ew")
        
        # Verdi-etikett
        self.gain_label = ttk.Label(controls_frame, text="1.0x", style='Dark.TLabel')
        self.gain_label.grid(row=1, column=2, padx=5, pady=(10, 0))
        
        # Oppdater etiketten når verdien endres
        self.gain_var.trace_add("write", self.update_gain_label)
        
        # Lagre valgt mikrofon
        self.selected_device = 0
        self.mic_dropdown.bind("<<ComboboxSelected>>", self.on_mic_selected)
        
        # Shortcut-informasjon
        shortcut_frame = ttk.Frame(controls_frame, style='Dark.TFrame')
        shortcut_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=(10, 0))
        
        ttk.Label(shortcut_frame, text=f"Tastatursnarvei:", style='Dark.TLabel').grid(row=0, column=0, sticky="w")
        ttk.Label(shortcut_frame, text=self.shortcut, style='Dark.TLabel', 
                font=("Arial", 10, "bold"), foreground=ACCENT_COLOR, background=DARK_BG).grid(row=0, column=1, sticky="w", padx=5)
        
        # Siste transkripsjon
        transcript_frame = ttk.LabelFrame(main_frame, text="Siste transkripsjon", style='Dark.TLabel')
        transcript_frame.grid(row=4, column=0, sticky="nsew", pady=(15, 10))
        transcript_frame.grid_columnconfigure(0, weight=1)
        transcript_frame.grid_rowconfigure(1, weight=1)
        
        # Legg til en fremdriftsindikator
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(transcript_frame, orient=tk.HORIZONTAL, 
                                     length=100, mode='indeterminate', 
                                     variable=self.progress_var)
        self.progress.grid(row=0, column=0, sticky="ew", padx=5, pady=2)
        self.progress.grid_remove()  # Skjul til vi trenger den
        
        # Transcript-tekst
        self.transcript_text = scrolledtext.ScrolledText(transcript_frame, height=10, 
                                                      bg="#2A2A2A", fg=TEXT_COLOR, 
                                                      font=("Arial", 11))
        self.transcript_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        
        # Loggområde
        log_frame = ttk.LabelFrame(main_frame, text="Logg", style='Dark.TLabel')
        log_frame.grid(row=5, column=0, sticky="nsew", pady=10)
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(0, weight=1)
        
        # Logg tekst
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, 
                                               bg="#2A2A2A", fg=SECONDARY_TEXT, 
                                               font=("Arial", 10))
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Logg oppstart
        self.log("Tale til Tekst startet")
        self.log(f"Hold inne '{self.shortcut}' for å ta opp tale")
    
    def show_settings(self):
        """Vis innstillinger"""
        # Sjekk om innstillingsvinduet allerede er åpent
        if hasattr(self, 'settings_window') and self.settings_window.winfo_exists():
            self.settings_window.focus_force()
            return
            
        # Opprett innstillingsvindu
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("Innstillinger")
        self.settings_window.geometry("500x400")
        self.settings_window.configure(bg=DARK_BG)
        self.settings_window.resizable(False, False)
        
        # Gjør vinduet modalt (blokkerer interaksjon med hovedvinduet)
        self.settings_window.grab_set()
        self.settings_window.transient(self.root)
        
        # Senter vinduet relativt til hovedvinduet
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (500 // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (400 // 2)
        self.settings_window.geometry(f"+{x}+{y}")
        
        # Hovedramme med padding
        main_frame = ttk.Frame(self.settings_window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Tittel
        title_label = ttk.Label(main_frame, text="Innstillinger", 
                               font=("Segoe UI", 16, "bold"))
        title_label.pack(anchor="w", pady=(0, 15))
        
        # Kategorifaner
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # --- Lydinnstillinger ---
        audio_frame = ttk.Frame(notebook, padding=10)
        notebook.add(audio_frame, text="Lyd")
        
        # Mikrofon-innstillinger
        mic_label = ttk.Label(audio_frame, text="Mikrofon:", anchor="w")
        mic_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        # Kopier mikrofonvalg fra hovedvinduet
        devices = sd.query_devices()
        input_devices = []
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                name = device['name']
                if len(name) > 40:
                    name = name[:37] + "..."
                input_devices.append((i, f"{name} ({device['max_input_channels']} kanaler)"))
        
        mic_dropdown = ttk.Combobox(audio_frame, width=40, state="readonly")
        mic_dropdown['values'] = [name for _, name in input_devices]
        mic_dropdown.grid(row=0, column=1, sticky="we", pady=(0, 5))
        
        # Sett til gjeldende valgt mikrofon
        for i, (idx, _) in enumerate(input_devices):
            if idx == self.selected_device:
                mic_dropdown.current(i)
                break
        
        # Lydnivå for opptak
        gain_label = ttk.Label(audio_frame, text="Opptaksnivå:", anchor="w")
        gain_label.grid(row=1, column=0, sticky="w", pady=(10, 5))
        
        gain_var = tk.DoubleVar(value=self.gain_var.get())
        gain_slider = ttk.Scale(audio_frame, from_=0.1, to=2.0, 
                               variable=gain_var, orient=tk.HORIZONTAL)
        gain_slider.grid(row=1, column=1, sticky="we", pady=(10, 5))
        
        gain_value = ttk.Label(audio_frame, text=f"{gain_var.get():.1f}x")
        gain_value.grid(row=1, column=2, sticky="w", padx=(5, 0), pady=(10, 5))
        
        def update_gain_label(*args):
            gain_value.configure(text=f"{gain_var.get():.1f}x")
        
        gain_var.trace_add("write", update_gain_label)
        
        # --- Transkripsjonsinnstillinger ---
        transcription_frame = ttk.Frame(notebook, padding=10)
        notebook.add(transcription_frame, text="Transkripsjon")
        
        # Språkvalg
        lang_label = ttk.Label(transcription_frame, text="Språk:", anchor="w")
        lang_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        lang_var = tk.StringVar(value="nb") # Norsk som standard
        langs = [("nb", "Norsk bokmål"), ("nn", "Norsk nynorsk"), 
                ("en", "Engelsk"), ("sv", "Svensk"), ("da", "Dansk")]
        
        lang_dropdown = ttk.Combobox(transcription_frame, width=40, state="readonly")
        lang_dropdown['values'] = [name for _, name in langs]
        lang_dropdown.current(0)
        lang_dropdown.grid(row=0, column=1, sticky="we", pady=(0, 5))
        
        # Modellstørrelse
        model_label = ttk.Label(transcription_frame, text="Modellstørrelse:", anchor="w")
        model_label.grid(row=1, column=0, sticky="w", pady=(10, 5))
        
        model_var = tk.StringVar(value="base")
        model_frame = ttk.Frame(transcription_frame)
        model_frame.grid(row=1, column=1, sticky="w", pady=(10, 5))
        
        ttk.Radiobutton(model_frame, text="Liten (rask)", 
                       variable=model_var, value="tiny").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(model_frame, text="Medium (standard)", 
                       variable=model_var, value="base").pack(side=tk.LEFT)
        
        # --- Grensesnitt ---
        ui_frame = ttk.Frame(notebook, padding=10)
        notebook.add(ui_frame, text="Grensesnitt")
        
        # Mørk/lys modus
        theme_label = ttk.Label(ui_frame, text="Tema:", anchor="w")
        theme_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        theme_var = tk.StringVar(value="dark")
        theme_frame = ttk.Frame(ui_frame)
        theme_frame.grid(row=0, column=1, sticky="w", pady=(0, 5))
        
        ttk.Radiobutton(theme_frame, text="Mørkt", 
                       variable=theme_var, value="dark").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(theme_frame, text="Lyst", 
                       variable=theme_var, value="light").pack(side=tk.LEFT)
        
        # Start minimert
        startup_var = tk.BooleanVar(value=False)
        startup_check = ttk.Checkbutton(ui_frame, text="Start minimert i systemfelt", 
                                      variable=startup_var)
        startup_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 5))
        
        # Alltid øverst
        topmost_var = tk.BooleanVar(value=False)
        topmost_check = ttk.Checkbutton(ui_frame, text="Hold vinduet alltid øverst", 
                                      variable=topmost_var)
        topmost_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=(5, 5))
        
        # --- Knapperad ---
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        
        # Lagre-knapp
        save_button = ttk.Button(button_frame, text="Lagre", 
                               command=lambda: self.save_settings(gain_var.get()))
        save_button.pack(side=tk.RIGHT, padx=(5, 0))
        
        # Avbryt-knapp
        cancel_button = ttk.Button(button_frame, text="Avbryt", 
                                command=self.settings_window.destroy)
        cancel_button.pack(side=tk.RIGHT)
        
        self.log("Viser innstillinger")
    
    def save_settings(self, gain_value):
        """Lagrer innstillinger"""
        if hasattr(self, 'settings_window'):
            # Lagre verdier her
            self.gain_var.set(gain_value)
            
            # Lukk innstillingsvinduet
            self.settings_window.destroy()
            
            self.log("Innstillinger lagret")
    
    def setup_tray(self):
        """Setter opp system tray-ikonet"""
        try:
            # Last ikon til system tray
            icon_image = None
            
            # Prøv å laste inn SVG eller PNG-ikon
            ikon_fil = os.path.join("resources", "icons", "app_icon")
            if os.path.exists(f"{ikon_fil}.svg") or os.path.exists(f"{ikon_fil}.png"):
                # Bruk PIL Image i stedet for PhotoImage for tray-ikonet
                if os.path.exists(f"{ikon_fil}.svg"):
                    png_data = BytesIO()
                    with open(f"{ikon_fil}.svg", 'rb') as svg_file:
                        svg_data = svg_file.read()
                        svg2png(bytestring=svg_data, write_to=png_data, 
                                output_width=64, output_height=64)
                    png_data.seek(0)
                    icon_image = Image.open(png_data)
                else:
                    icon_image = Image.open(f"{ikon_fil}.png")
            else:
                # Lag et enkelt placeholder-ikon hvis ingen ikoner finnes
                icon_image = Image.new('RGBA', (64, 64), (0, 120, 212, 255))
                icon_image.save(f"{ikon_fil}.png")
                
            # Definer meny for system tray
            menu = (
                pystray.MenuItem('Vis', self.show_window),
                pystray.MenuItem('Avslutt', self.exit_app)
            )
            
            # Opprett ikonet 
            self.tray_icon = pystray.Icon("tale_til_tekst", icon_image, "Tale til Tekst", menu)
            self.tray_icon.default_action = self.show_window
            
            # Start ikonet i en egen tråd
            t = threading.Thread(target=self.tray_icon.run, daemon=True)
            t.start()
        except Exception as e:
            print(f"Kunne ikke opprette system tray-ikon: {e}")
    
    def position_window_at_tray(self):
        """Plasserer vinduet nederst til høyre"""
        try:
            self.root.update_idletasks()
            
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            window_width = max(600, self.root.winfo_width())
            window_height = max(900, self.root.winfo_height())
            
            position_x = screen_width - window_width - 20
            position_y = screen_height - window_height - 40
            
            self.root.geometry(f"+{position_x}+{position_y}")
        except Exception as e:
            print(f"Feil ved posisjonering av vindu: {e}")
    
    def show_window(self, *args):
        """Viser applikasjonsvinduet"""
        self.minimized_to_tray = False
        self.root.deiconify()
        self.root.update_idletasks()

        if self.root.state() == 'iconic':
            self.root.state('normal')
        
        self.position_window_at_tray()
        
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.root.after(200, lambda: self.root.attributes("-topmost", False))
        
        self.log("Viser hovedvindu")
    
    def on_close(self):
        """Håndterer når brukeren lukker vinduet"""
        self.minimize_to_tray()
    
    def minimize_to_tray(self):
        """Minimerer applikasjonen til system tray"""
        self.minimized_to_tray = True
        self.root.withdraw()
        self.log("Minimert til systemfelt")
    
    def exit_app(self):
        """Avslutter applikasjonen"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()
    
    def log(self, message):
        """Logg en melding til loggområdet"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def update_status(self, message, is_recording=False):
        """Oppdater statusmelding"""
        if is_recording:
            self.status_var.set(f"Opptak pågår... {message}")
            self.status_label.configure(foreground=ERROR_COLOR)
        else:
            self.status_var.set(message)
            self.status_label.configure(foreground=TEXT_COLOR)
            
        if message.startswith("Transkriberer"):
            if not self.is_transcribing:
                self.is_transcribing = True
                self.start_progress()
        else:
            if self.is_transcribing:
                self.is_transcribing = False
                self.stop_progress()
    
    def set_recording(self, is_recording):
        """Sett opptaksstatus"""
        self.is_recording = is_recording
        if is_recording:
            self.update_status("Opptak pågår...", True)
            self.log("Opptak startet - snakk tydelig")
            self.start_progress()
        else:
            self.update_status("Transkriberer...", False)
            self.log("Opptak stoppet - transkriberer")
    
    def start_progress(self):
        """Start fremdriftsindikator"""
        self.progress.grid()
        self.progress.start(10)
    
    def stop_progress(self):
        """Stopp fremdriftsindikator"""
        self.progress.stop()
        self.progress.grid_remove()
    
    def show_transcription(self, text):
        """Vis transkribert tekst"""
        self.transcription_count += 1
        self.transcript_text.delete(1.0, tk.END)
        self.transcript_text.insert(tk.END, text)
        self.update_status("Klar", False)
    
    def update_model_status(self, loaded=False, error=False):
        """Oppdaterer statusmelding for modell"""
        if error:
            self.model_status_var.set("Modellstatus: FEIL")
            self.model_status.configure(foreground=ERROR_COLOR)
        elif loaded:
            self.model_status_var.set("Modellstatus: Lastet")
            self.model_status.configure(foreground=SUCCESS_COLOR)
        else:
            self.model_status_var.set("Modellstatus: Laster...")
            self.model_status.configure(foreground=WARNING_COLOR)
    
    def update_microphones(self):
        """Oppdaterer listen over tilgjengelige mikrofoner"""
        try:
            devices = sd.query_devices()
            input_devices = []
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    name = device['name']
                    if len(name) > 40:
                        name = name[:37] + "..."
                    input_devices.append((i, f"{name} ({device['max_input_channels']} kanaler)"))
            
            self.mic_dropdown['values'] = [name for _, name in input_devices]
            self.device_ids = [idx for idx, _ in input_devices]
            
            if input_devices:
                self.mic_dropdown.current(0)
                self.selected_device = self.device_ids[0]
                self.update_device_sample_rate(self.selected_device)
                self.log(f"Fant {len(input_devices)} mikrofoner/inngangsenheter")
                
                current_device = devices[self.selected_device]
                self.log(f"Aktiv mikrofon: {current_device['name']}")
                self.log(f"Sample rate: {self.device_sample_rate} Hz")
            else:
                self.log("Ingen mikrofoner funnet!")
                
        except Exception as e:
            self.log(f"Feil ved oppdatering av mikrofoner: {e}")
    
    def update_device_sample_rate(self, device_id):
        """Oppdaterer sample rate basert på den valgte enheten"""
        try:
            device_info = sd.query_devices(device_id, 'input')
            default_sr = int(device_info['default_samplerate'])
            
            if default_sr in SUPPORTED_RATES:
                self.device_sample_rate = default_sr
            else:
                for rate in SUPPORTED_RATES:
                    try:
                        sd.check_input_settings(device=device_id, samplerate=rate)
                        self.device_sample_rate = rate
                        break
                    except:
                        continue
                else:
                    self.device_sample_rate = default_sr
            
            self.log(f"Enhet {device_id} bruker sample rate: {self.device_sample_rate} Hz")
            
            if self.device_sample_rate != 16000:
                self.log("Merk: Opptak vil bli resampled til 16000 Hz for Whisper")
                
        except Exception as e:
            self.log(f"Feil ved oppdatering av sample rate: {e}")
            self.device_sample_rate = 16000
    
    def on_mic_selected(self, event):
        """Håndterer valg av mikrofon"""
        if self.device_ids:
            selected_index = self.mic_dropdown.current()
            if 0 <= selected_index < len(self.device_ids):
                self.selected_device = self.device_ids[selected_index]
                self.update_device_sample_rate(self.selected_device)
                
                device_info = sd.query_devices(self.selected_device, 'input')
                self.log(f"Byttet til mikrofon: {device_info['name']}")
    
    def test_microphone(self):
        """Test den valgte mikrofonen"""
        self.log("Starter mikrofontest...")
        self.run_mic_test_callback()
    
    def update_gain_label(self, *args):
        """Oppdaterer etiketten for gain-verdien"""
        gain = self.gain_var.get()
        self.gain_label.configure(text=f"{gain:.1f}x")
        
    def run_mic_test_callback(self):
        """Placeholder for mikrofontest-callback"""
        pass

    def make_window_movable(self):
        """Gjør vinduet flyttbart med musen"""
        def on_press(event):
            self.x = event.x
            self.y = event.y
            
        def on_drag(event):
            x = self.root.winfo_x() + event.x - self.x
            y = self.root.winfo_y() + event.y - self.y
            self.root.geometry(f"+{x}+{y}")
            
        self.root.bind("<ButtonPress-1>", on_press)
        self.root.bind("<B1-Motion>", on_drag)