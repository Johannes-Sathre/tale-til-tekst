#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Brukergrensesnittmodul

Moderne brukergrensesnitt for Tale til Tekst-applikasjonen
"""

import os
import time
import threading
import tkinter as tk
from tkinter import ttk
import numpy as np
import pystray
from PIL import Image, ImageTk
from ctypes import windll, byref, c_int, sizeof

# Importer fra våre egne moduler
from config import *
from utils import last_ikon, save_svg_icon, setup_icons

# UI komponenter
class ModernButton(tk.Frame):
    """Moderne knapp med ikon-støtte"""
    def __init__(self, parent, text, command=None, width=120, height=36, style="default", corner_radius=6):
        super().__init__(parent, width=width, height=height, bg=DARK_BG)
        self.pack_propagate(False)  # Behold angitt størrelse
        
        # Tilstand og funksjoner
        self.command = command
        self.width = width
        self.height = height
        self.text = text
        self.icon = None
        self.style = style
        self.corner_radius = corner_radius
        self.state = "normal"  # Legg til state-egenskap (normal/disabled)
        
        # Knappens bakgrunn
        self.canvas = tk.Canvas(self, bg=DARK_BG, highlightthickness=0, 
                               width=width, height=height)
        self.canvas.pack(fill="both", expand=True)
        
        # Bestem farger basert på stil
        if style == "accent":
            bg_color = ACCENT_COLOR
            hover_color = ACCENT_HOVER
            text_col = "#FFFFFF"
            border_col = ACCENT_COLOR
        else:
            bg_color = DARKER_BG
            hover_color = ACCENT_COLOR
            text_col = TEXT_COLOR
            border_col = BORDER_COLOR
            
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_col = text_col
        self.border_col = border_col
        self.disabled_bg = DARKER_BG
        self.disabled_text = SECONDARY_TEXT
        self.disabled_border = BORDER_COLOR
        
        # Tegn bakgrunn med avrundede hjørner
        if corner_radius > 0:
            # Tegn avrundede hjørner med arc
            self.bg = self.draw_rounded_rect(2, 2, width-2, height-2, 
                                         corner_radius, bg_color, border_col)
        else:
            # Vanlig rektangel hvis corner_radius er 0
            self.bg = self.canvas.create_rectangle(
                2, 2, width-2, height-2, fill=bg_color, outline=border_col
            )
        
        # Legg til tekst
        self.text_x = width//2  # Standard tekstposisjon (midtstilt)
        self.text_obj = self.canvas.create_text(
            self.text_x, height//2, text=text, fill=text_col,
            font=("Segoe UI", 11), anchor="center"
        )
        
        # Bind hendelser
        self.canvas.bind("<Enter>", self.on_enter)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
    
    def config(self, **kwargs):
        """Støtte for config-metoden"""
        if "state" in kwargs:
            self.state = kwargs.pop("state")  # Fjern state før vi sender videre
            self._update_appearance()
        # Send resten av parametrene videre til superklassen
        if kwargs:
            return super().config(**kwargs)
        return None
        
    def configure(self, **kwargs):
        """Alias for config"""
        return self.config(**kwargs)
    
    def _update_appearance(self):
        """Oppdater knappens utseende basert på tilstand"""
        if self.state == "disabled":
            # Deaktivert tilstand
            self.canvas.itemconfig(self.bg, fill=self.disabled_bg, outline=self.disabled_border)
            self.canvas.itemconfig(self.text_obj, fill=self.disabled_text)
        else:
            # Normal tilstand
            self.canvas.itemconfig(self.bg, fill=self.bg_color, outline=self.border_col)
            self.canvas.itemconfig(self.text_obj, fill=self.text_col)
    
    def draw_rounded_rect(self, x1, y1, x2, y2, radius, fill_color, outline_color):
        """Tegn et rektangel med avrundede hjørner"""
        points = [
            x1+radius, y1,
            x2-radius, y1,
            x2, y1,
            x2, y1+radius,
            x2, y2-radius,
            x2, y2,
            x2-radius, y2,
            x1+radius, y2,
            x1, y2,
            x1, y2-radius,
            x1, y1+radius,
            x1, y1
        ]
        
        return self.canvas.create_polygon(points, fill=fill_color, outline=outline_color, smooth=True)
    
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
        """Mus over knappen"""
        if self.state == "disabled":
            return
            
        if self.style == "accent":
            self.canvas.itemconfig(self.bg, fill=ACCENT_HOVER)
        else:
            self.canvas.itemconfig(self.bg, fill=ACCENT_COLOR)
        
    def on_leave(self, event):
        """Mus forlater knappen"""
        if self.state == "disabled":
            return
            
        if self.style == "accent":
            self.canvas.itemconfig(self.bg, fill=ACCENT_COLOR)
        else:
            self.canvas.itemconfig(self.bg, fill=DARKER_BG)
        
    def on_click(self, event):
        """Klikk på knappen"""
        if self.state == "disabled":
            return
            
        self.canvas.itemconfig(self.bg, fill=ACCENT_HOVER)
        
    def on_release(self, event):
        """Slipp musknappen"""
        if self.state == "disabled":
            return
            
        if self.style == "accent":
            self.canvas.itemconfig(self.bg, fill=ACCENT_COLOR)
        else:
            self.canvas.itemconfig(self.bg, fill=DARKER_BG)
        if self.command:
            self.command()

class CardPanel(tk.Frame):
    """En panelkomponent med moderne stil"""
    def __init__(self, parent, title="", width=None, height=None, icon=None):
        super().__init__(parent, bg=CARD_BG, bd=0, highlightthickness=0)
        
        # Avrundede hjørner og skygge-effekt
        self.round_rectangle_frame = tk.Frame(self, bg=CARD_BG, bd=1,
                                           highlightbackground=CARD_BORDER,
                                           highlightthickness=1)
        self.round_rectangle_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Tittelramme
        title_frame = tk.Frame(self.round_rectangle_frame, bg=DARKER_PANEL, height=42)
        title_frame.pack(fill="x", side="top")
        
        # Tittel med ikon hvis tilgjengelig
        title_pad = 12
        if icon:
            icon_label = tk.Label(title_frame, image=icon, bg=DARKER_PANEL)
            icon_label.pack(side="left", padx=(12, 0))
            title_pad = 6
            
        self.title_label = tk.Label(title_frame, text=title, bg=DARKER_PANEL, 
                                  fg=TEXT_COLOR, font=("Segoe UI", 12, "bold"))
        self.title_label.pack(side="left", padx=title_pad, pady=6)
        
        # Innholdsramme
        self.content_frame = tk.Frame(self.round_rectangle_frame, bg=CARD_BG)
        self.content_frame.pack(fill="both", expand=True, padx=15, pady=15)

class StatusIndicator(tk.Canvas):
    """Status indikator"""
    def __init__(self, parent, size=12, status_type="success"):
        super().__init__(parent, width=size, height=size, bg=CARD_BG, 
                       highlightthickness=0)
        
        self.size = size
        self.set_status(status_type)
        
    def set_status(self, status_type):
        """Sett statustype (success, warning, error)"""
        self.delete("all")
        
        if status_type == "success":
            color = SUCCESS_COLOR
        elif status_type == "warning":
            color = WARNING_COLOR
        else:
            color = ERROR_COLOR
            
        # Tegn en fylt sirkel
        self.create_oval(2, 2, self.size-2, self.size-2, 
                       fill=color, outline="")

class TaleApp:
    def __init__(self, root, shortcut, recorder=None, transcriber=None):
        self.root = root
        self.shortcut = shortcut
        self.recorder = recorder
        self.transcriber = transcriber
        
        # Konfigurer applikasjonen
        if self.recorder:
            self.recorder.set_app(self)
        if self.transcriber:
            self.transcriber.set_app(self)
        
        # Sett opp state
        self.is_recording = False
        self.transcription_count = 0
        self.selected_device = 0  # Standard mikrofon
        self.device_sample_rate = SAMPLE_RATE  # Standard sample rate
        self.is_transcribing = False  # For å spore transkripsjonsstatus
        self.device_ids = []  # Holder oversikt over enhet-IDer
        
        # Sett opp ikoner
        setup_icons({
            "microphone": MICROPHONE_SVG,
            "keyboard": KEYBOARD_SVG,
            "close": CLOSE_SVG,
            "settings": SETTINGS_SVG
        })
        
        # Opprett GUI
        self.setup_gui()
        
        # System tray-variabler
        self.tray_icon = None
        self.minimized_to_tray = False
        
        # Oppdater mikrofoner ved oppstart
        self.update_microphones()
        
        # Oppsett av system tray
        self.setup_tray()
        
        # Håndter lukkeknappen (X)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Plasser vinduet over system tray (nederst til høyre) med en lenger forsinkelse
        # for å sikre at vinduet er opprettet og har korrekt størrelse
        self.root.after(300, self.position_window_at_tray)
    
    def setup_gui(self):
        """Sett opp brukergrensesnittet"""
        self.root.title(APP_NAME)
        
        # Øk størrelsen med 40%
        self.root.geometry("840x1120")
        self.root.minsize(840, 1120)
        
        # Sett bakgrunnsfarge
        self.root.configure(bg=DARK_BG)
        
        # Fjern standard tittellinjen
        self.root.overrideredirect(True)
        
        # Gi vinduet avrundede hjørner (Windows-spesifikt)
        if os.name == 'nt':  # Sjekk om vi er på Windows
            try:
                hwnd = windll.user32.GetParent(self.root.winfo_id())
                # Øk verdien for mer avrundede hjørner (fra 2 til 8)
                windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, byref(c_int(24)), sizeof(c_int))
            except Exception as e:
                print(f"Kunne ikke sette avrundede hjørner: {e}")
        
        # Gjør vinduet flyttbart med musen
        self.make_window_movable()
        
        # Prøv å laste app-ikon
        try:
            app_icon = last_ikon("app_icon", 32)
            self.root.iconphoto(True, app_icon)
        except Exception as e:
            print(f"Kunne ikke laste app-ikon: {e}")
        
        # Hovedramme med skygge-effekt
        main_frame = tk.Frame(self.root, bg=DARK_BG, highlightbackground="#000000", 
                           highlightthickness=1)
        main_frame.pack(fill="both", expand=True)
        
        # Tittelbar
        title_bar = tk.Frame(main_frame, bg=HEADER_BG, height=48)
        title_bar.pack(fill="x")
        
        # App-tittel
        title_label = tk.Label(title_bar, text=APP_NAME, bg=HEADER_BG, 
                             fg=TEXT_COLOR, font=("Segoe UI", 13, "bold"))
        title_label.pack(side="left", padx=15, pady=10)
        
        # Lukkeknapp
        self.close_icon = last_ikon("close", 16)
        
        close_btn = tk.Button(title_bar, image=self.close_icon, bg=HEADER_BG, 
                            activebackground=ERROR_COLOR, bd=0, 
                            highlightthickness=0, command=self.on_close)
        close_btn.pack(side="right", padx=15, pady=10)
        
        # Horisontal linje under tittelbar
        divider = tk.Frame(main_frame, bg=DIVIDER_COLOR, height=1)
        divider.pack(fill="x")
        
        # Hovedinnholdsområde
        content_container = tk.Frame(main_frame, bg=DARK_BG)
        content_container.pack(fill="both", expand=True)
        
        self.main_content = tk.Frame(content_container, bg=DARK_BG)
        self.main_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Modellstatuspanel
        model_panel = CardPanel(self.main_content, title="Modellstatus")
        model_panel.pack(fill="x", pady=(0, 15))
        
        # Modellstatus i panelet
        status_frame = tk.Frame(model_panel.content_frame, bg=CARD_BG)
        status_frame.pack(fill="x")
        
        # Statusindikator
        self.model_indicator = StatusIndicator(status_frame, status_type="warning")
        self.model_indicator.pack(side="left", padx=5)
        
        self.status_var = tk.StringVar(value="Laster modell...")
        self.status_label = tk.Label(status_frame, textvariable=self.status_var, 
                                   font=("Segoe UI", 11, "bold"), 
                                   bg=CARD_BG, fg=WARNING_COLOR)
        self.status_label.pack(side="left", padx=5)
        
        # Modellstatus
        self.model_status_var = tk.StringVar(value="Modellstatus: Laster...")
        self.model_status = tk.Label(status_frame, textvariable=self.model_status_var, 
                                   font=("Segoe UI", 10), bg=CARD_BG, fg=WARNING_COLOR)
        self.model_status.pack(side="right", padx=5)
        
        # Modellvalg
        model_select_frame = tk.Frame(model_panel.content_frame, bg=CARD_BG)
        model_select_frame.pack(fill="x", pady=5)
        
        tk.Label(model_select_frame, text="Velg modell:", bg=CARD_BG, fg=TEXT_COLOR).pack(side="left", padx=5)
        
        from config import AVAILABLE_WHISPER_MODELS, DEFAULT_WHISPER_MODEL
        self.model_dropdown = ttk.Combobox(model_select_frame, width=30, state="readonly", font=("Segoe UI", 11))
        self.model_dropdown['values'] = AVAILABLE_WHISPER_MODELS
        self.model_dropdown.set(DEFAULT_WHISPER_MODEL)
        self.model_dropdown.pack(side="left", padx=5)
        
        # Last modell-knapp
        self.load_model_btn = ModernButton(model_select_frame, "Last inn modell", 
                                      command=self.load_selected_model, width=200, height=36, 
                                      corner_radius=8, style="accent")
        self.load_model_btn.pack(side="right", padx=10)
        
        # Mikrofon-panel
        mic_panel = CardPanel(self.main_content, title="Mikrofon")
        mic_panel.pack(fill="x", pady=(0, 15))
        
        # Mikrofon-valg i panelet
        mic_frame = tk.Frame(mic_panel.content_frame, bg=CARD_BG)
        mic_frame.pack(fill="x", pady=5)
        
        # Mikrofon dropdown med stilfull stil
        tk.Label(mic_frame, text="Enhet:", bg=CARD_BG, fg=TEXT_COLOR).pack(side="left", padx=5)
        
        self.mic_dropdown = ttk.Combobox(mic_frame, width=45, state="readonly", font=("Segoe UI", 11))
        self.mic_dropdown.pack(side="left", padx=5)
        self.mic_dropdown.bind("<<ComboboxSelected>>", self.on_mic_selected)
        
        # Last mikrofonikon
        mic_icon = last_ikon("microphone", 16)
        
        # Test mikrofon-knapp
        self.test_mic_btn = ModernButton(mic_panel.content_frame, "Test mikrofon", 
                                     command=self.test_microphone, width=200, height=42, 
                                     corner_radius=8, style="accent")
        if mic_icon:
            self.test_mic_btn.set_icon(mic_icon)
        self.test_mic_btn.pack(pady=15)
        
        # Følsomhet-kontroll
        gain_frame = tk.Frame(mic_panel.content_frame, bg=CARD_BG)
        gain_frame.pack(fill="x", pady=5)
        
        tk.Label(gain_frame, text="Følsomhet:", bg=CARD_BG, fg=TEXT_COLOR).pack(side="left", padx=5)
        
        self.gain_var = tk.DoubleVar(value=1.0)
        self.gain_scale = ttk.Scale(gain_frame, from_=0.1, to=5.0, 
                                 orient=tk.HORIZONTAL, variable=self.gain_var,
                                 length=250)
        self.gain_scale.pack(side="left", padx=5, fill="x", expand=True)
        
        # Verdi-etikett
        self.gain_label = tk.Label(gain_frame, text="1.0x", bg=CARD_BG, fg=TEXT_COLOR)
        self.gain_label.pack(side="left", padx=5)
        
        # Oppdater etiketten når verdien endres
        self.gain_var.trace_add("write", self.update_gain_label)
        
        # Snarvei-panel
        shortcut_panel = CardPanel(self.main_content, title="Tastatursnarvei")
        shortcut_panel.pack(fill="x", pady=(0, 15))
        
        # Snarvei-info
        shortcut_frame = tk.Frame(shortcut_panel.content_frame, bg=CARD_BG)
        shortcut_frame.pack(fill="x", pady=5)
        
        # Last tastaturikonet
        keyboard_icon = last_ikon("keyboard", 16)
        
        if keyboard_icon:
            keyboard_label = tk.Label(shortcut_frame, image=keyboard_icon, bg=CARD_BG)
            keyboard_label.pack(side="left", padx=5)
        
        self.shortcut_label = tk.Label(shortcut_frame, text=f"{self.shortcut}", 
                                    font=("Segoe UI", 12, "bold"), 
                                    bg=CARD_BG, fg=ACCENT_COLOR)
        self.shortcut_label.pack(side="left", padx=5, pady=5)
        
        # OpenAI korrekturpanel
        openai_panel = CardPanel(self.main_content, title="OpenAI Korrektur")
        openai_panel.pack(fill="x", pady=(0, 15))
        
        # API-nøkkel input
        api_frame = tk.Frame(openai_panel.content_frame, bg=CARD_BG)
        api_frame.pack(fill="x", pady=5)
        
        tk.Label(api_frame, text="API-nøkkel:", bg=CARD_BG, fg=TEXT_COLOR).pack(side="left", padx=5)
        
        self.api_key_var = tk.StringVar(value=OPENAI_API_KEY)
        self.api_key_entry = tk.Entry(api_frame, textvariable=self.api_key_var, 
                                   width=40, font=("Segoe UI", 11), 
                                   show="•")  # Skjul teksten med prikker
        self.api_key_entry.pack(side="left", padx=5, pady=5)
        
        # Oppdater API-nøkkel når den endres
        self.api_key_var.trace_add("write", self.update_api_key)
        
        # Vis/skjul knapp for API-nøkkel
        self.show_key = tk.BooleanVar(value=False)
        
        def toggle_api_key_visibility():
            if self.show_key.get():
                self.api_key_entry.config(show="")
            else:
                self.api_key_entry.config(show="•")
        
        show_key_check = tk.Checkbutton(api_frame, text="Vis nøkkel", 
                                      variable=self.show_key,
                                      command=toggle_api_key_visibility,
                                      bg=CARD_BG, fg=TEXT_COLOR, 
                                      selectcolor=DARKER_PANEL,
                                      activebackground=CARD_BG,
                                      activeforeground=TEXT_COLOR)
        show_key_check.pack(side="left", padx=5)
        
        # Aktiver korrektur checkbox
        enable_frame = tk.Frame(openai_panel.content_frame, bg=CARD_BG)
        enable_frame.pack(fill="x", pady=5)
        
        self.enable_correction = tk.BooleanVar(value=False)
        correction_check = tk.Checkbutton(enable_frame, 
                                        text="Aktiver OpenAI korrektur av transkripsjoner", 
                                        variable=self.enable_correction,
                                        bg=CARD_BG, fg=TEXT_COLOR, 
                                        selectcolor=DARKER_PANEL,
                                        activebackground=CARD_BG,
                                        activeforeground=TEXT_COLOR)
        correction_check.pack(side="left", padx=5, pady=5)
        
        # Info om korrektur
        info_label = tk.Label(openai_panel.content_frame, 
                           text=("OpenAI API brukes til å korrigere og forbedre transkripsjoner. "
                                "Dette krever en gyldig API-nøkkel og internettforbindelse."),
                           bg=CARD_BG, fg=SECONDARY_TEXT, 
                           font=("Segoe UI", 9), wraplength=720, justify="left")
        info_label.pack(fill="x", padx=5, pady=5)
        
        # Transkripsjonspanel
        transcript_panel = CardPanel(self.main_content, title="Siste transkripsjon")
        transcript_panel.pack(fill="both", expand=True, pady=(0, 15))
        
        # Fremdriftsindikator
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(transcript_panel.content_frame, orient=tk.HORIZONTAL, 
                                     length=100, mode='indeterminate', 
                                     variable=self.progress_var)
        self.progress.pack(fill="x", padx=5, pady=2)
        self.progress.pack_forget()  # Skjul til vi trenger den
        
        # Transkripsjonstekst
        self.transcript_text = tk.Text(transcript_panel.content_frame, height=10, 
                                   bg=CARD_BG, fg=TEXT_COLOR, bd=0,
                                   font=("Segoe UI", 12))
        self.transcript_text.pack(fill="both", expand=True, pady=5)
        
        # Loggpanel
        log_panel = CardPanel(self.main_content, title="Logg")
        log_panel.pack(fill="both", expand=True)
        
        # Loggområde
        self.log_text = tk.Text(log_panel.content_frame, height=10, 
                             bg=CARD_BG, fg=SECONDARY_TEXT, bd=0,
                             font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True)
        
        # Versjonsinformasjon i bunnen
        version_frame = tk.Frame(self.main_content, bg=DARK_BG)
        version_frame.pack(fill="x", pady=(10, 0))

        version_label = tk.Label(version_frame, text=f"Versjon: {APP_VERSION}", 
                               bg=DARK_BG, fg=SECONDARY_TEXT, font=("Segoe UI", 8))
        version_label.pack(side="right", padx=5)
        
        # Konfigurer TTK stil
        self.setup_ttk_styles()
        
        # Logg oppstart
        self.log(f"{APP_NAME} startet")
        self.log(f"Hold inne '{self.shortcut}' for å ta opp tale")
        
    def setup_ttk_styles(self):
        """Sett opp TTK-stiler for bedre utseende"""
        style = ttk.Style()
        
        # Komboboks
        style.configure("TCombobox", 
                      fieldbackground=DARKER_PANEL, 
                      background=DARKER_PANEL,
                      foreground=TEXT_COLOR,
                      darkcolor=ACCENT_COLOR,
                      lightcolor=ACCENT_COLOR,
                      arrowcolor=TEXT_COLOR,
                      font=("Segoe UI", 11))
        
        # Skyvekontroll
        style.configure("TScale",
                      background=CARD_BG,
                      troughcolor=DARKER_PANEL,
                      slidercolor=ACCENT_COLOR)
        
        # Progressbar
        style.configure("TProgressbar",
                      background=ACCENT_COLOR,
                      troughcolor=DARKER_PANEL)
    
    def setup_tray(self):
        """Setter opp system tray-ikonet"""
        try:
            # Last ikon til system tray
            icon_image = None
            
            # Prøv å laste inn SVG eller PNG-ikon
            ikon_fil = os.path.join("resources", "icons", "app_icon")
            if os.path.exists(f"{ikon_fil}.svg") or os.path.exists(f"{ikon_fil}.png"):
                # Bruk PIL Image for tray-ikonet
                if os.path.exists(f"{ikon_fil}.svg"):
                    from io import BytesIO
                    from cairosvg import svg2png
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
            self.tray_icon = pystray.Icon(APP_NAME, icon_image, APP_NAME, menu)
            self.tray_icon.default_action = self.show_window
            
            # Start ikonet i en egen tråd
            t = threading.Thread(target=self.tray_icon.run, daemon=True)
            t.start()
        except Exception as e:
            print(f"Kunne ikke opprette system tray-ikon: {e}")
    
    def position_window_at_tray(self):
        """Plasserer vinduet nederst til høyre"""
        try:
            # Sikre at vinduet er synlig og at GUI er oppdatert
            self.root.update_idletasks()
            
            # Hent skjermstørrelse
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Sett foretrukket størrelse hvis vinduet ikke har korrekt størrelse
            if self.root.winfo_width() < 100 or self.root.winfo_height() < 100:
                # Vinduet har ikke fått riktig størrelse ennå, bruk geometrien vi satte
                window_width = 840
                window_height = 1120
            else:
                # Bruk faktisk vindusstørrelse
                window_width = self.root.winfo_width()
                window_height = self.root.winfo_height()
            
            # Beregn posisjon (nederst til høyre, med marger)
            position_x = screen_width - window_width - 20
            position_y = screen_height - window_height - 40
            
            # Juster for å unngå plasseringer utenfor skjermen
            if position_x < 0:
                position_x = 0
            if position_y < 0:
                position_y = 0
                
            # Sett vinduets posisjon
            self.root.geometry(f"+{position_x}+{position_y}")
            
            # Logg posisjonering, men bruk print() ved oppstart
            if hasattr(self, 'log_text'):
                self.log(f"Vindu posisjonert: {window_width}x{window_height} ved posisjon {position_x},{position_y}")
            else:
                print(f"Vindu posisjonert: {window_width}x{window_height} ved posisjon {position_x},{position_y}")
            
        except Exception as e:
            print(f"Feil ved posisjonering av vindu: {e}")
    
    def show_window(self, *args):
        """Viser applikasjonsvinduet"""
        self.minimized_to_tray = False
        self.root.deiconify()
        
        # Tving oppdatering av vinduet
        self.root.update_idletasks()

        if self.root.state() == 'iconic':
            self.root.state('normal')
        
        # Bruk samme posisjonering som ved oppstart
        self.position_window_at_tray()
        
        self.root.attributes("-topmost", True)
        self.root.focus_force()
        self.root.after(200, lambda: self.root.attributes("-topmost", False))
        
        self.log("Viser hovedvindu i standardposisjon")

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
        
        # Skriv alltid til standardutgangen
        print(f"[{timestamp}] {message}")
        
        # Skriv til loggområdet hvis det er tilgjengelig
        if hasattr(self, 'log_text') and self.log_text.winfo_exists():
            try:
                self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
                self.log_text.see(tk.END)
            except Exception as e:
                # Feilsikring hvis widget er ødelagt eller ikke tilgjengelig
                print(f"Kunne ikke logge til tekstområde: {e}")
    
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
        self.progress.pack(fill="x", padx=5, pady=2)
        self.progress.start(10)
    
    def stop_progress(self):
        """Stopp fremdriftsindikator"""
        self.progress.stop()
        self.progress.pack_forget()
    
    def show_transcription(self, text):
        """Vis transkribert tekst"""
        self.transcription_count += 1
        
        if text and self.enable_correction.get():
            # Lagre API-nøkkelen i konfigurasjonen
            from config import OPENAI_API_KEY
            current_api_key = self.api_key_var.get()
            
            # Hvis API-nøkkelen er tom eller mangler, vis bare vanlig transkripsjon
            if not current_api_key:
                self.log("OpenAI korrektur er aktivert, men ingen API-nøkkel er angitt.")
                self.transcript_text.delete(1.0, tk.END)
                self.transcript_text.insert(tk.END, text)
                self.update_status("Klar", False)
                return
                
            # Vis at vi starter korrektur
            self.log("Starter OpenAI korrektur...")
            self.update_status("Korrigerer med OpenAI...", False)
            self.start_progress()
            
            # Bruk en separat tråd for å unngå å fryse grensesnittet
            import threading
            from utils import correct_text_with_openai
            
            def correction_thread():
                try:
                    # Korriger teksten med OpenAI
                    self.log("Sender transkripsjon til OpenAI for korrektur...")
                    corrected_text = correct_text_with_openai(text, current_api_key, verbose=True)
                    
                    # Oppdater GUI fra hovedtråden
                    def update_gui():
                        if corrected_text:
                            # Beregn antall endringer (enkel sammenligning)
                            orig_words = text.split()
                            corr_words = corrected_text.split()
                            
                            # Enkel beregning av endringer
                            total_words = max(len(orig_words), len(corr_words))
                            changed = sum(1 for i in range(min(len(orig_words), len(corr_words))) if orig_words[i] != corr_words[i])
                            changed += abs(len(orig_words) - len(corr_words))  # Legg til manglende/ekstra ord
                            
                            if changed > 0:
                                change_percent = (changed / total_words) * 100
                                self.log(f"OpenAI korrektur fullført med ca. {changed} endringer ({change_percent:.1f}% av teksten)")
                            else:
                                self.log("OpenAI korrektur fullført uten endringer")
                            
                            # Vis både original og korrigert transkripsjon
                            self.transcript_text.delete(1.0, tk.END)
                            self.transcript_text.insert(tk.END, f"ORIGINAL:\n{text}\n\nKORRIGERT:\n{corrected_text}")
                        else:
                            # Hvis korrektur feilet, vis bare originalen
                            self.transcript_text.delete(1.0, tk.END)
                            self.transcript_text.insert(tk.END, text)
                            self.log("OpenAI korrektur feilet. Viser original transkripsjon.")
                        
                        self.stop_progress()
                        self.update_status("Klar", False)
                    
                    # Oppdater GUI i hovedtråden
                    self.root.after(0, update_gui)
                    
                except Exception as e:
                    # Ved feil, logg og vis original tekst
                    def handle_error():
                        self.log(f"Feil under korrektur: {e}")
                        self.transcript_text.delete(1.0, tk.END)
                        self.transcript_text.insert(tk.END, text)
                        self.stop_progress()
                        self.update_status("Klar", False)
                    
                    self.root.after(0, handle_error)
            
            # Start en tråd for korrektur
            threading.Thread(target=correction_thread, daemon=True).start()
        else:
            # Ingen korrektur, vis bare vanlig transkripsjon
            self.transcript_text.delete(1.0, tk.END)
            self.transcript_text.insert(tk.END, text)
            self.update_status("Klar", False)
    
    def update_model_status(self, loaded=False, error=False):
        """Oppdater modellstatus i GUI"""
        if error:
            # Ved feil
            self.status_var.set("Feil ved lasting")
            self.model_status_var.set("Modell: Ikke lastet")
            self.model_indicator.set_status("error")
            self.status_label.configure(fg=ERROR_COLOR)
            self.model_status.configure(fg=ERROR_COLOR)
        elif loaded:
            # Når modellen er lastet
            current_model = self.transcriber.get_current_model() if self.transcriber else "unknown"
            self.status_var.set("Modell lastet")
            self.model_status_var.set(f"Modell: {current_model}")
            self.model_indicator.set_status("success")
            self.status_label.configure(fg=SUCCESS_COLOR)
            self.model_status.configure(fg=SUCCESS_COLOR)
        else:
            # Under lasting
            current_model = self.transcriber.get_current_model() if self.transcriber else "unknown"
            self.status_var.set("Laster modell...")
            self.model_status_var.set(f"Modell: {current_model} (laster...)")
            self.model_indicator.set_status("warning")
            self.status_label.configure(fg=WARNING_COLOR)
            self.model_status.configure(fg=WARNING_COLOR)
    
    def update_microphones(self):
        """Oppdaterer listen over tilgjengelige mikrofoner"""
        try:
            import sounddevice as sd
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
            import sounddevice as sd
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
            
            if self.device_sample_rate != SAMPLE_RATE:
                self.log(f"Merk: Opptak vil bli resampled til {SAMPLE_RATE} Hz for Whisper")
                
        except Exception as e:
            self.log(f"Feil ved oppdatering av sample rate: {e}")
            self.device_sample_rate = SAMPLE_RATE
    
    def on_mic_selected(self, event):
        """Håndterer valg av mikrofon"""
        if self.device_ids:
            selected_index = self.mic_dropdown.current()
            if 0 <= selected_index < len(self.device_ids):
                self.selected_device = self.device_ids[selected_index]
                self.update_device_sample_rate(self.selected_device)
                
                import sounddevice as sd
                device_info = sd.query_devices(self.selected_device, 'input')
                self.log(f"Byttet til mikrofon: {device_info['name']}")
    
    def test_microphone(self):
        """Test den valgte mikrofonen"""
        self.log("Starter mikrofontest...")
        if self.recorder:
            # Bruk recorder for å teste mikrofonen
            threading.Thread(target=self.recorder.test_microphone, daemon=True).start()
        else:
            self.log("Feil: Recorder ikke tilgjengelig!")
    
    def update_gain_label(self, *args):
        """Oppdater etiketten for mikrofonforsterkning"""
        self.gain_label.config(text=f"{self.gain_var.get():.1f}x")
    
    def load_selected_model(self):
        """Last inn den valgte Whisper-modellen"""
        selected_model = self.model_dropdown.get()
        if not selected_model:
            return
        
        self.log(f"Endrer modell til: {selected_model}...")
        
        # Deaktiver knappen mens modellen lastes
        self.load_model_btn.config(state="disabled")
        
        # Oppdater status
        self.update_status("Laster modell...", False)
        self.status_var.set("Laster modell...")
        self.model_status_var.set(f"Modell: {selected_model} (laster...)")
        self.model_indicator.set_status("warning")
        
        # Bruk en separat tråd for å laste inn modellen
        import threading
        
        def load_model_thread():
            # Last inn modellen med det nye modellnavnet
            if self.transcriber:
                self.transcriber.load_model(selected_model)
                
                # Aktiver knappen igjen etter lasting
                self.root.after(0, lambda: self.load_model_btn.config(state="normal"))
        
        # Start tråden
        loading_thread = threading.Thread(target=load_model_thread)
        loading_thread.daemon = True
        loading_thread.start()
    
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

    def update_api_key(self, *args):
        """Oppdater API-nøkkel når den endres"""
        # Få gjeldende API-nøkkel fra inndatafeltet
        api_key = self.api_key_var.get().strip()
        
        # Oppdater global variabel for API-nøkkel
        import sys
        # Bruk importlib for å unngå importproblemer med sirkelmessig import
        if sys.version_info >= (3, 4):
            import importlib
            import config
            config.OPENAI_API_KEY = api_key
            importlib.reload(config)
        else:
            # For eldre Python-versjoner
            import config
            config.OPENAI_API_KEY = api_key
            
        # Logg endringen bare hvis API-nøkkel er satt eller endret
        if api_key:
            masked_key = api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else "****"
            self.log(f"API-nøkkel oppdatert: {masked_key}")
        # Ikke logg tom API-nøkkel for å unngå støy i loggen