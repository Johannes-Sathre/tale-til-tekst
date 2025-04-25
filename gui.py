#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - GUI-modul

Brukergrensesnitt for Tale til Tekst-applikasjonen
"""

import os
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import numpy as np
import sounddevice as sd
import pystray
from PIL import Image, ImageDraw
import keyboard

# Konstanter
SAMPLE_RATE = 16000  # 16kHz
CHANNELS = 1  # Mono
SUPPORTED_RATES = [48000, 44100, 22050, 16000, 8000]  # Mulige sample rates i prioritert rekkefølge

class TaleApp:
    def __init__(self, root, shortcut):
        self.root = root
        self.shortcut = shortcut
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
        
    def setup_gui(self):
        """Sett opp brukergrensesnittet"""
        self.root.title("Tale til Tekst")
        self.root.geometry("600x450")
        self.root.minsize(600, 450)
        
        # Sett app-ikon (hvis tilgjengelig)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # Hovedramme
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status-etikett
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT)
        
        self.status_var = tk.StringVar(value="Laster modell...")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 12, "bold"))
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Modellstatus
        self.model_status_var = tk.StringVar(value="Modellstatus: Laster...")
        self.model_status = ttk.Label(status_frame, textvariable=self.model_status_var, 
                                    font=("Arial", 10), foreground="blue")
        self.model_status.pack(side=tk.RIGHT, padx=10)
        
        # Mikrofon-valg
        mic_frame = ttk.LabelFrame(main_frame, text="Velg mikrofon")
        mic_frame.pack(fill=tk.X, pady=5)
        
        mic_settings_frame = ttk.Frame(mic_frame)
        mic_settings_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.mic_dropdown = ttk.Combobox(mic_settings_frame, width=40, state="readonly")
        self.mic_dropdown.pack(side=tk.LEFT, padx=5)
        
        button_frame = ttk.Frame(mic_settings_frame)
        button_frame.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = ttk.Button(button_frame, text="Oppdater", command=self.update_microphones)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        test_btn = ttk.Button(button_frame, text="Test mikrofon", command=self.test_microphone)
        test_btn.pack(side=tk.LEFT, padx=2)
        
        # Følsomhet (gain) kontroll
        gain_frame = ttk.Frame(mic_frame)
        gain_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(gain_frame, text="Følsomhet:").pack(side=tk.LEFT, padx=5)
        
        self.gain_var = tk.DoubleVar(value=1.0)
        self.gain_scale = ttk.Scale(gain_frame, from_=0.1, to=5.0, 
                                 orient=tk.HORIZONTAL, variable=self.gain_var,
                                 length=250)
        self.gain_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Verdi-etikett
        self.gain_label = ttk.Label(gain_frame, text="1.0x")
        self.gain_label.pack(side=tk.LEFT, padx=5)
        
        # Oppdater etiketten når verdien endres
        self.gain_var.trace_add("write", self.update_gain_label)
        
        # Lagre valgt enhet
        self.selected_device = 0
        self.mic_dropdown.bind("<<ComboboxSelected>>", self.on_mic_selected)
        
        # Snarvei-informasjon
        shortcut_frame = ttk.Frame(main_frame)
        shortcut_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(shortcut_frame, text=f"Tastatursnarvei: {self.shortcut}").pack(side=tk.LEFT)
        
        # Legg til minimer til system tray-knapp
        ttk.Button(shortcut_frame, text="Minimer til systemfelt", 
                 command=self.minimize_to_tray).pack(side=tk.RIGHT)
        
        # Loggområde
        log_frame = ttk.LabelFrame(main_frame, text="Logg")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Siste transkripsjon
        transcript_frame = ttk.LabelFrame(main_frame, text="Siste transkripsjon")
        transcript_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Legg til en fremdriftsindikator
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(transcript_frame, orient=tk.HORIZONTAL, 
                                     length=100, mode='indeterminate', 
                                     variable=self.progress_var)
        self.progress.pack(fill=tk.X, padx=5, pady=2)
        self.progress.pack_forget()  # Skjul til vi trenger den
        
        self.transcript_text = scrolledtext.ScrolledText(transcript_frame, height=5)
        self.transcript_text.pack(fill=tk.BOTH, expand=True)
        
        # Nedre knapper
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Avslutt", command=self.root.destroy).pack(side=tk.RIGHT)
        
        # Oppsett av stil
        self.setup_styles()
        
        # Logg oppstart
        self.log("Tale til Tekst startet")
        self.log(f"Hold inne '{self.shortcut}' for å ta opp tale")
        
    def setup_tray(self):
        """Setter opp system tray-ikonet"""
        # Opprett et enkelt bilde for ikonet
        icon_image = self.create_icon_image()
        
        # Definer meny for system tray
        menu = (
            pystray.MenuItem('Vis', self.show_window),
            pystray.MenuItem('Test mikrofon', self.test_microphone_from_tray),
            pystray.MenuItem('Avslutt', self.exit_app)
        )
        
        # Opprett ikonet
        self.tray_icon = pystray.Icon("tale_til_tekst", icon_image, "Tale til Tekst", menu)
        
        # Start ikonet i en egen tråd
        t = threading.Thread(target=self.tray_icon.run, daemon=True)
        t.start()
        
    def create_icon_image(self):
        """Lager et enkelt bilde for system tray-ikonet"""
        # Prøv å laste et ikon fra fil først
        try:
            if os.path.exists("icon.png"):
                return Image.open("icon.png")
        except:
            pass
            
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
    
    def show_window(self):
        """Viser applikasjonsvinduet fra system tray"""
        if self.minimized_to_tray:
            self.minimized_to_tray = False
            self.root.deiconify()  # Vis vinduet
            self.root.lift()  # Bring vinduet til forgrunnen
    
    def on_close(self):
        """Håndterer når brukeren lukker vinduet"""
        # Minimer til system tray i stedet for å avslutte
        self.minimize_to_tray()
    
    def exit_app(self):
        """Avslutter applikasjonen fullstendig"""
        # Rydd opp system tray-ikonet
        if self.tray_icon:
            self.tray_icon.stop()
        
        # Ødelegg hovedvinduet og avslutt programmet
        self.root.destroy()
    
    def test_microphone_from_tray(self):
        """Kalles når brukeren velger 'Test mikrofon' fra system tray-menyen"""
        # Vis vinduet hvis det er minimert
        self.show_window()
        
        # Vent litt så vinduet vises
        self.root.after(200, self.test_microphone)
    
    def setup_styles(self):
        """Sett opp stiler for GUI-elementer"""
        self.recording_style = {'background': 'red', 'foreground': 'white', 'font': ('Arial', 12, 'bold')}
        self.normal_style = {'background': self.root.cget('background'), 'foreground': 'black', 'font': ('Arial', 12, 'bold')}
    
    def log(self, message):
        """Legg til melding i loggområdet"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        print(message)
    
    def update_status(self, message, is_recording=False):
        """Oppdater statusetiketten"""
        self.status_var.set(message)
        
        if is_recording:
            self.status_label.configure(**self.recording_style)
            self.root.configure(background='#ffdddd')
            
            # Oppdater system tray-ikonet (blinke)
            if self.tray_icon:
                # Endrer ikke ikonet ennå, kan implementeres senere
                self.tray_icon.title = "Tale til Tekst (OPPTAK)"
        else:
            self.status_label.configure(**self.normal_style)
            self.root.configure(background=self.normal_style['background'])
            
            # Nullstill system tray-ikonet
            if self.tray_icon:
                self.tray_icon.title = "Tale til Tekst"
            
        self.root.update()
    
    def set_recording(self, is_recording):
        """Sett opptaksstatus"""
        self.is_recording = is_recording
        if is_recording:
            self.update_status("OPPTAK PÅGÅR", True)
            self.log("Opptak startet")
        else:
            self.update_status("Transkriberer...", False)
            self.log("Opptak stoppet, transkriberer...")
            # Start fremdriftsindikator
            self.start_progress()
    
    def start_progress(self):
        """Start fremdriftsindikator"""
        self.is_transcribing = True
        self.progress.pack(fill=tk.X, padx=5, pady=2)
        self.progress.start(10)  # 10ms mellom oppdateringer

    def stop_progress(self):
        """Stopp fremdriftsindikator"""
        self.is_transcribing = False
        self.progress.stop()
        self.progress.pack_forget()

    def show_transcription(self, text):
        """Vis transkripsjonen i GUI"""
        self.transcription_count += 1
        self.transcript_text.delete(1.0, tk.END)
        self.transcript_text.insert(tk.END, text)
        self.log(f"Transkripsjon #{self.transcription_count} fullført ({len(text)} tegn)")
        self.update_status("Klar", False)

    def update_model_status(self, loaded=False, error=False):
        """Oppdater visning av modellstatus"""
        if error:
            self.model_status_var.set("Modellstatus: FEIL")
            self.model_status.configure(foreground="red")
        elif loaded:
            self.model_status_var.set("Modellstatus: Klar")
            self.model_status.configure(foreground="green")
        else:
            self.model_status_var.set("Modellstatus: Laster...")
            self.model_status.configure(foreground="blue")
        self.root.update()

    def update_microphones(self):
        """Oppdater listen over tilgjengelige mikrofoner"""
        try:
            devices = sd.query_devices()
            mic_list = []
            
            # Finn alle inngangsenheter (mikrofoner)
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    name = f"{i}: {device['name']}"
                    mic_list.append(name)
            
            if not mic_list:
                self.log("Ingen mikrofoner funnet!")
                return
            
            # Oppdater dropdown-liste
            self.mic_dropdown['values'] = mic_list
            
            # Velg første mikrofon som standard hvis ingen er valgt
            if not self.mic_dropdown.get():
                self.mic_dropdown.current(0)
                self.selected_device = int(mic_list[0].split(':')[0])
                self.log(f"Valgt mikrofon: {mic_list[0]}")
                # Oppdater sample rate for denne enheten
                self.update_device_sample_rate(self.selected_device)
        except Exception as e:
            self.log(f"Feil ved oppdatering av mikrofoner: {e}")

    def update_device_sample_rate(self, device_id):
        """Oppdater sample rate for valgt enhet til en verdi som støttes"""
        try:
            device_info = sd.query_devices(device_id, 'input')
            default_rate = int(device_info['default_samplerate'])
            
            self.log(f"Mikrofon støtter {default_rate} Hz som standard")
            
            # Sjekk om standard sample rate er i våre støttede verdier
            if default_rate in SUPPORTED_RATES:
                self.device_sample_rate = default_rate
            else:
                # Prøv å finne best mulig sample rate
                for rate in SUPPORTED_RATES:
                    try:
                        # Test om denne sample rate fungerer
                        sd.check_input_settings(device=device_id, samplerate=rate, channels=CHANNELS)
                        self.device_sample_rate = rate
                        self.log(f"Bruker sample rate: {rate} Hz")
                        break
                    except Exception:
                        continue
            
            # Oppdater status
            self.log(f"Mikrofon sample rate satt til: {self.device_sample_rate} Hz")
            
        except Exception as e:
            self.log(f"Feil ved oppdatering av sample rate: {e}")
            self.device_sample_rate = 44100  # Fallback til vanlig verdi
            self.log(f"Bruker standard sample rate: 44100 Hz")

    def on_mic_selected(self, event):
        """Håndterer valg av mikrofon"""
        selected = self.mic_dropdown.get()
        if selected:
            try:
                device_id = int(selected.split(':')[0])
                self.selected_device = device_id
                self.log(f"Byttet til mikrofon: {selected}")
                # Oppdater sample rate for denne enheten
                self.update_device_sample_rate(device_id)
            except Exception as e:
                self.log(f"Feil ved valg av mikrofon: {e}")

    def test_microphone(self):
        """Test valgt mikrofon"""
        # Sjekk om modellen er lastet (denne sjekken gjøres i recorder.py)
        # Vi henviser til en callback-funksjon som vil bli implementert i recorder.py
        self.log(f"Tester mikrofon (ID: {self.selected_device})...")
        self.update_status("Tester mikrofon...", False)
        
        # Callback vil bli satt opp av recorder.py
        if hasattr(self, 'run_mic_test_callback') and callable(self.run_mic_test_callback):
            threading.Thread(target=self.run_mic_test_callback, daemon=True).start()
        else:
            self.log("Mikrofon-testfunksjon ikke tilgjengelig")
            self.update_status("Kan ikke teste mikrofon", False)

    def update_gain_label(self, *args):
        """Oppdater etiketten for følsomhet"""
        value = self.gain_var.get()
        self.gain_label.config(text=f"{value:.1f}x") 