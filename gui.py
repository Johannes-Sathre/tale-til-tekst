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
from PIL import Image, ImageDraw, ImageTk
import keyboard

# Konstanter
SAMPLE_RATE = 16000  # 16kHz
CHANNELS = 1  # Mono
SUPPORTED_RATES = [48000, 44100, 22050, 16000, 8000]  # Mulige sample rates i prioritert rekkefølge

# Farger og stiler
DARK_BG = "#202020"
ACCENT_COLOR = "#0078D7"
TEXT_COLOR = "#FFFFFF"
SECONDARY_TEXT = "#AAAAAA"
BORDER_COLOR = "#333333"
HOVER_COLOR = "#303030"
SUCCESS_COLOR = "#4CAF50"
WARNING_COLOR = "#FFC107"
ERROR_COLOR = "#F44336"

class ModernButton(tk.Canvas):
    """Moderne knapp med hover-effekt"""
    def __init__(self, parent, text, icon=None, command=None, width=120, height=40, bg=DARK_BG, fg=TEXT_COLOR, 
                 active_bg=HOVER_COLOR, active_fg=TEXT_COLOR, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg, highlightthickness=0, **kwargs)
        self.text = text
        self.command = command
        self.bg = bg
        self.fg = fg
        self.active_bg = active_bg
        self.active_fg = active_fg
        self.icon_image = icon
        self.active = False
        
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        
        self.draw()
        
    def draw(self):
        self.delete("all")
        fill = self.active_bg if self.active else self.bg
        text_color = self.active_fg if self.active else self.fg
        
        # Tegn bakgrunn
        self.create_rectangle(0, 0, self.winfo_width(), self.winfo_height(), fill=fill, outline="")
        
        # Tegn tekst
        if self.icon_image:
            img_margin = 5
            text_x = img_margin*2 + 24  # Juster for ikonbredde
            # Tegn ikon til venstre for teksten
            self.create_image(img_margin + 12, self.winfo_height()//2, image=self.icon_image)
        else:
            text_x = self.winfo_width()//2
            
        self.create_text(text_x, self.winfo_height()//2, text=self.text, 
                        fill=text_color, anchor="w" if self.icon_image else "center")
    
    def on_enter(self, event):
        self.active = True
        self.draw()
        
    def on_leave(self, event):
        self.active = False
        self.draw()
        
    def on_click(self, event):
        if self.command:
            self.command()

class TaleApp:
    def __init__(self, root, shortcut):
        self.root = root
        self.shortcut = shortcut
        # Bildecache
        self.images = {}
        self.setup_gui()
        self.is_recording = False
        self.transcription_count = 0
        self.selected_device = 0  # Standard mikrofon
        self.device_sample_rate = SAMPLE_RATE  # Standard sample rate
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
        # Gjør dette til slutt etter at alt er opprettet og initialisert
        self.position_window_at_tray()
        
    def setup_gui(self):
        """Sett opp brukergrensesnittet"""
        self.root.title("Tale til Tekst")
        self.root.geometry("800x700")
        self.root.minsize(600, 600)
        self.root.configure(bg=DARK_BG)
        
        # Gjør vinduet flyttbart med musen
        self.root.overrideredirect(True)  # Fjern standardtittellinje
        self.make_window_movable()
        
        # Sett app-ikon
        try:
            self.root.iconbitmap("icon.ico")
        except Exception as e:
            print(f"Kunne ikke laste ikon: {e}")
            pass
        
        # Lag rektangel for runding av hjørner
        style = ttk.Style()
        style.configure('Dark.TFrame', background=DARK_BG)
        style.configure('Dark.TLabel', background=DARK_BG, foreground=TEXT_COLOR)
        style.configure('Dark.TButton', background=DARK_BG, foreground=TEXT_COLOR)
        
        # Konfigurerer main_frame til å bruke vekter for å støtte responsiv layout
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        
        # Hovedramme
        main_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Konfigurer main_frame til å være responsiv
        rows, cols = 6, 1  # Antall rader og kolonner
        for i in range(cols):
            main_frame.grid_columnconfigure(i, weight=1)
        # Gi forskjellige vekter til ulike rader
        main_frame.grid_rowconfigure(0, weight=0)  # Tittel
        main_frame.grid_rowconfigure(1, weight=0)  # Status
        main_frame.grid_rowconfigure(2, weight=0)  # Knapper
        main_frame.grid_rowconfigure(3, weight=0)  # Mikrofon
        main_frame.grid_rowconfigure(4, weight=1)  # Transkripsjon
        main_frame.grid_rowconfigure(5, weight=1)  # Logg
        
        # Toppramme med tittel og lukkeknapp
        top_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        top_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        top_frame.grid_columnconfigure(0, weight=1)  # Tittelen skal strekke seg
        
        title_label = ttk.Label(top_frame, text="Tale til Tekst", style='Dark.TLabel', font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, sticky="w")
        
        # Lage et kryss-ikon for lukkeknappen
        close_canvas = tk.Canvas(top_frame, width=30, height=30, bg=DARK_BG, highlightthickness=0)
        close_canvas.grid(row=0, column=1, sticky="e")
        close_canvas.create_line(10, 10, 20, 20, fill=TEXT_COLOR, width=2)
        close_canvas.create_line(10, 20, 20, 10, fill=TEXT_COLOR, width=2)
        close_canvas.bind("<Button-1>", lambda e: self.minimize_to_tray())
        
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
        
        # Modus-knapper (F.eks. Laste inn modell, Test mikrofon, etc.)
        modes_frame = ttk.Frame(main_frame, style='Dark.TFrame')
        modes_frame.grid(row=2, column=0, sticky="ew", pady=10)
        modes_frame.grid_columnconfigure(0, weight=1)
        modes_frame.grid_columnconfigure(1, weight=1)
        
        # Lag ikoner for knapper
        mic_icon = self.create_icon("microphone", "#FFFFFF")
        settings_icon = self.create_icon("settings", "#FFFFFF")
        
        # Knapper i moderne stil
        self.mic_button = ModernButton(modes_frame, "Test mikrofon", icon=mic_icon, 
                                     command=self.test_microphone, width=380, height=40)
        self.mic_button.grid(row=0, column=0, padx=(0, 10), sticky="w")
        
        self.settings_button = ModernButton(modes_frame, "Innstillinger", icon=settings_icon,
                                         command=self.show_settings, width=380, height=40)
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
    
    def create_icon(self, icon_type, color):
        """Lag ikoner for brukergrensesnittet"""
        size = 16
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        if icon_type == "microphone":
            # Tegn en mikrofon
            draw.rectangle([6, 4, 10, 10], fill=color)
            draw.ellipse([5, 3, 11, 6], fill=color)
            draw.rectangle([7, 10, 9, 12], fill=color)
            draw.rectangle([5, 12, 11, 13], fill=color)
        elif icon_type == "settings":
            # Tegn et tannhjul
            # Ytre sirkel
            draw.ellipse([3, 3, 13, 13], outline=color, width=1)
            # Indre sirkel
            draw.ellipse([6, 6, 10, 10], fill=color)
            # Tagger
            for i in range(8):
                angle = i * 45
                x1 = 8 + 7 * np.cos(np.radians(angle))
                y1 = 8 + 7 * np.sin(np.radians(angle))
                x2 = 8 + 4 * np.cos(np.radians(angle))
                y2 = 8 + 4 * np.sin(np.radians(angle))
                draw.line([x1, y1, x2, y2], fill=color, width=1)
        
        photo = ImageTk.PhotoImage(img)
        # Lagre en referanse for å unngå garbage collection
        if icon_type not in self.images:
            self.images[icon_type] = photo
            
        return photo
    
    def show_settings(self):
        """Vis innstillinger"""
        # Implementer en innstillingsdialog her
        self.log("Innstillinger kommer i neste versjon")
    
    def setup_tray(self):
        """Setter opp system tray-ikonet"""
        # Opprett et enkelt bilde for ikonet
        icon_image = self.create_icon_image()
        
        # Definerer vår egen handler for å håndtere klikk
        def on_left_click(icon, item):
            # Denne kalles når "Vis" velges fra menyen eller når ikonet venstreklikkes
            print("Vis applikasjon valgt")
            self.show_window()
        
        # Definer meny for system tray (vises ved høyreklikk)
        menu = (
            pystray.MenuItem('Vis', on_left_click),  # Bruk vår lokale funksjon 
            pystray.MenuItem('Avslutt', self.exit_app)
        )
        
        # Opprett ikonet med default action for venstreklikk
        self.tray_icon = pystray.Icon(
            "tale_til_tekst", 
            icon_image, 
            "Tale til Tekst", 
            menu
        )
        
        # Spesielt for pystray: Sett default action til å være menypunktet "Vis"
        # Dette gjør at venstreklikk utfører samme handling som å velge "Vis" fra menyen
        self.tray_icon.default_action = on_left_click
        
        # Start ikonet i en egen tråd
        t = threading.Thread(target=self.tray_icon.run, daemon=True)
        t.start()
        
    def create_icon_image(self):
        """Lager et enkelt bilde for system tray-ikonet"""
        # Prøv å laste et ikon fra fil først
        try:
            if os.path.exists("tray_icon.png"):
                return Image.open("tray_icon.png")
            elif os.path.exists("icon_64.png"):
                return Image.open("icon_64.png")
            elif os.path.exists("icon.png"):
                return Image.open("icon.png")
        except Exception as e:
            self.log(f"Kunne ikke laste tray-ikon: {e}")
            
        # Hvis ingen fil finnes, lag et enkelt ikon
        width = 64
        height = 64
        color1 = (0, 120, 212)  # Blå
        color2 = (255, 255, 255)  # Hvit
        
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)
        
        # Tegn en sirkel med mikrofon-symbol
        dc.ellipse((0, 0, width, height), fill=color1)
        
        # Tegn en mikrofon-form
        mic_width = width // 3
        mic_height = height // 2
        mic_x = (width - mic_width) // 2
        mic_y = (height - mic_height) // 3
        
        # Mikrofon-kropp
        dc.rectangle((mic_x, mic_y, mic_x + mic_width, mic_y + mic_height), fill=color2)
        
        # Mikrofon-base
        base_width = mic_width * 1.5
        base_height = height // 10
        base_x = (width - base_width) // 2
        base_y = mic_y + mic_height + height // 10
        
        dc.rectangle((base_x, base_y, base_x + base_width, base_y + base_height), fill=color2)
        
        # Forbindelse
        connector_width = width // 10
        connector_x = (width - connector_width) // 2
        dc.rectangle((connector_x, mic_y + mic_height, connector_x + connector_width, base_y), fill=color2)
        
        return image
    
    def minimize_to_tray(self):
        """Minimerer applikasjonen til system tray"""
        self.minimized_to_tray = True
        self.root.withdraw()  # Skjul vinduet
        self.log("Minimert til systemfelt")
    
    def position_window_at_tray(self):
        """Plasserer vinduet over system tray (nederst til høyre)"""
        try:
            # Oppdater UI før vi beregner
            self.root.update_idletasks()
            
            # Hent skjermstørrelse
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            
            # Hent vindustørrelse (fra enten gjeldende størrelse eller ønsket størrelse)
            try:
                window_width = self.root.winfo_width()
                window_height = self.root.winfo_height()
                
                # Hvis vinduet ikke er synlig ennå, bruk standardstørrelser
                if window_width < 100 or window_height < 100:
                    window_width = 800
                    window_height = 700
            except:
                window_width = 800
                window_height = 700
            
            # Beregn posisjon (nederst til høyre)
            position_x = screen_width - window_width - 20  # 20px fra høyre kant
            position_y = screen_height - window_height - 40  # 40px fra bunnen (plass til taskbar)
            
            # Sett posisjon
            self.root.geometry(f"+{position_x}+{position_y}")
            
            # Ikke forsøk å logge her - det kan forårsake feil under oppstart
            print(f"Vindu posisjonert: {window_width}x{window_height} på {position_x},{position_y}")
        except Exception as e:
            # Bruk print istedenfor self.log for å unngå rekursiv feil
            print(f"Feil ved posisjonering av vindu: {e}")
    
    def show_window(self, *args):
        """Viser applikasjonsvinduet fra system tray"""
        try:
            # Merk at vi ikke sjekker self.minimized_to_tray lenger, bare vis vinduet
            self.minimized_to_tray = False
            
            # Vis vinduet (deiconify setter vinduet til normaltilstand)
            self.root.deiconify()
            self.root.update_idletasks()  # Oppdater UI

            # Fiks Windows-spesifikk bug der vinduet kan bli gjemt
            if self.root.state() == 'iconic':  # Hvis fortsatt minimert
                self.root.state('normal')
            
            # Plasser vinduet over system tray
            self.position_window_at_tray()
            
            # Flytt vinduet til forgrunnen og gi det fokus
            self.root.attributes("-topmost", True)
            self.root.lift()
            self.root.focus_force()
            self.root.after(200, lambda: self.root.attributes("-topmost", False))  # Fjern topmost etter en kort stund
            
            self.log("Viser hovedvindu")
        except Exception as e:
            print(f"Feil ved visning av vindu: {e}")
    
    def on_close(self):
        """Håndterer når brukeren lukker vinduet"""
        # Minimer til system tray i stedet for å avslutte
        self.minimize_to_tray()
    
    def test_microphone_from_tray(self):
        """Test mikrofonen fra system tray"""
        self.show_window()
        self.test_microphone()
    
    def exit_app(self):
        """Avslutter applikasjonen"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()
    
    def log(self, message):
        """Logg en melding til loggområdet"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)  # Rull til bunnen
    
    def update_status(self, message, is_recording=False):
        """Oppdater statusmelding"""
        if is_recording:
            self.status_var.set(f"Opptak pågår... {message}")
            self.status_label.configure(foreground=ERROR_COLOR)
        else:
            self.status_var.set(message)
            self.status_label.configure(foreground=TEXT_COLOR)
            
        # Start eller stopp fremdriftsindikatoren basert på om vi transkriberer
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
        self.progress.grid()  # Vis progressbar
        self.progress.start(10)
    
    def stop_progress(self):
        """Stopp fremdriftsindikator"""
        self.progress.stop()
        self.progress.grid_remove()  # Skjul progressbar
    
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
            
            # Finn alle inngangsenheter (mikrofoner)
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    name = device['name']
                    if len(name) > 40:
                        name = name[:37] + "..."
                    input_devices.append((i, f"{name} ({device['max_input_channels']} kanaler)"))
            
            # Oppdater nedtrekkslisten
            self.mic_dropdown['values'] = [name for _, name in input_devices]
            
            # Lagre enhetenes ID-er for senere bruk
            self.device_ids = [idx for idx, _ in input_devices]
            
            if input_devices:
                self.mic_dropdown.current(0)
                self.selected_device = self.device_ids[0]
                self.update_device_sample_rate(self.selected_device)
                self.log(f"Fant {len(input_devices)} mikrofoner/inngangsenheter")
                
                # Logg gjeldende mikrofon
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
            
            # Finn nærmeste støttede sample rate
            if default_sr in SUPPORTED_RATES:
                self.device_sample_rate = default_sr
            else:
                # Sjekk om enheten støtter noen av våre foretrukne rater
                supported_sr = None
                
                for rate in SUPPORTED_RATES:
                    try:
                        sd.check_input_settings(device=device_id, samplerate=rate)
                        supported_sr = rate
                        break
                    except:
                        continue
                
                if supported_sr:
                    self.device_sample_rate = supported_sr
                else:
                    # Bruk enhetens standard hvis ingen av de foretrukne fungerer
                    self.device_sample_rate = default_sr
            
            self.log(f"Enhet {device_id} bruker sample rate: {self.device_sample_rate} Hz")
            
            # Sjekk om vi må resample
            if self.device_sample_rate != 16000:
                self.log("Merk: Opptak vil bli resampled til 16000 Hz for Whisper")
                
        except Exception as e:
            self.log(f"Feil ved oppdatering av sample rate: {e}")
            self.device_sample_rate = 16000  # Fall tilbake til standard
    
    def on_mic_selected(self, event):
        """Håndterer valg av mikrofon"""
        if self.device_ids:
            selected_index = self.mic_dropdown.current()
            if 0 <= selected_index < len(self.device_ids):
                self.selected_device = self.device_ids[selected_index]
                self.update_device_sample_rate(self.selected_device)
                
                # Logg det nye valget
                device_info = sd.query_devices(self.selected_device, 'input')
                self.log(f"Byttet til mikrofon: {device_info['name']}")
    
    def test_microphone(self):
        """Test den valgte mikrofonen"""
        # Bruk callback fra recorder-modulen
        self.log("Starter mikrofontest...")
        self.run_mic_test_callback()
    
    def update_gain_label(self, *args):
        """Oppdaterer etiketten for gain-verdien"""
        gain = self.gain_var.get()
        self.gain_label.configure(text=f"{gain:.1f}x")
    
    def on_tray_icon_click(self, icon, button):
        """Håndterer klikk på system tray-ikonet"""
        try:
            # Skriv til konsoll for debugging
            print(f"Tray ikon klikket med: {button}")
            
            # Sjekk om det er venstreklikk (button kan variere mellom plattformer)
            if str(button) == "Button.left" or button.name == "left":
                # Vi må sørge for at dette kjøres på hovedtråden
                # siden det er GUI-operasjoner
                if self.root:
                    # Forsøk å kjøre show_window på flere måter for sikkerhet
                    try:
                        # Metode 1: Direkte kall
                        self.show_window()
                    except Exception as e1:
                        print(f"Metode 1 feilet: {e1}")
                        try:
                            # Metode 2: Bruk etter-metoden for å kjøre på hovedtråden
                            self.root.after(100, self.show_window)
                        except Exception as e2:
                            print(f"Metode 2 feilet: {e2}")
                            # Prøv å gjøre grunnleggende operasjoner manuelt
                            try:
                                self.root.deiconify()
                                self.root.lift()
                                self.root.focus_force()
                            except Exception as e3:
                                print(f"Fallback metode feilet: {e3}")
        except Exception as e:
            print(f"Feil i tray icon click handler: {e}") 