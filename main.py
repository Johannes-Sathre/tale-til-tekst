#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst

En applikasjon som konverterer tale til tekst ved å bruke faster-whisper modellen.
Programmet tar opp tale når en global tastatursnarvei (Ctrl+Alt+S) holdes inne.
Når snarveien slippes, transkriberes talen til tekst og limes automatisk inn.

Utviklet for Windows 10/11 med Python 3.9/3.10.
Krever mikrofon og minimum 8GB RAM for optimal ytelse.

Versjon: 1.0.0
Dato: 2024
Lisens: MIT
"""

import os
import sys
import threading
import tempfile
import time
import numpy as np
import sounddevice as sd
import keyboard
import pyperclip
import tkinter as tk
from tkinter import ttk, scrolledtext
from scipy import signal  # Brukes til resampling
from faster_whisper import WhisperModel  # Bruk faster-whisper igjen

# Konfigurasjon
SHORTCUT = "ctrl+alt+s"  # Standard snarvei, kan endres
SAMPLE_RATE = 16000  # 16kHz
CHANNELS = 1  # Mono

# Globale variabler
recording = False
temp_file = None
recording_data = []
whisper_model = None
model_loaded = False  # Ny global variabel for å spore om modellen er lastet
app = None
SUPPORTED_RATES = [48000, 44100, 22050, 16000, 8000]  # Mulige sample rates i prioritert rekkefølge

class TaleApp:
    def __init__(self, root):
        self.root = root
        self.setup_gui()
        self.is_recording = False
        self.transcription_count = 0
        self.selected_device = 0  # Standard mikrofon
        self.device_sample_rate = SAMPLE_RATE  # Standard sample rate
        self.is_transcribing = False  # For å spore transkripsjonsstatus
        
        # Oppdater mikrofoner ved oppstart
        self.update_microphones()
        
    def setup_gui(self):
        """Sett opp brukergrensesnittet"""
        self.root.title("Tale til Tekst")
        self.root.geometry("600x450")
        self.root.minsize(600, 450)
        
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
        
        ttk.Label(shortcut_frame, text=f"Tastatursnarvei: {SHORTCUT}").pack(side=tk.LEFT)
        
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
        self.log(f"Hold inne '{SHORTCUT}' for å ta opp tale")
        
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
        else:
            self.status_label.configure(**self.normal_style)
            self.root.configure(background=self.normal_style['background'])
            
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
        if not model_loaded:
            self.log("Kan ikke teste mikrofon: Venter på at modellen lastes")
            return
        
        self.log(f"Tester mikrofon (ID: {self.selected_device})...")
        self.update_status("Tester mikrofon...", False)
        
        # Start en kort testopptak i en separat tråd
        threading.Thread(target=self.run_mic_test, daemon=True).start()

    def run_mic_test(self):
        """Kjør en test av mikrofonen"""
        test_data = []
        test_duration = 3  # 3 sekunder test
        
        def test_callback(indata, frames, time, status):
            test_data.append(indata.copy())
        
        try:
            # Start et kort opptak med riktig sample rate
            with sd.InputStream(samplerate=self.device_sample_rate, channels=CHANNELS, 
                             device=self.selected_device, callback=test_callback):
                # Vis nedtelling
                for i in range(test_duration, 0, -1):
                    self.root.after(0, lambda i=i: self.update_status(f"Tester mikrofon... {i}", False))
                    time.sleep(1)
            
            # Sjekk om vi fikk noe data
            if test_data:
                # Beregn lydnivå (amplitude)
                audio_data = np.concatenate(test_data)
                amplitude = np.abs(audio_data).mean() * 100
                
                if amplitude < 0.01:
                    self.log(f"Advarsel: Veldig lavt lydnivå ({amplitude:.4f}). Sjekk at mikrofonen fungerer.")
                    self.root.after(0, lambda: self.update_status("Mikrofon OK, men lavt signal", False))
                else:
                    self.log(f"Mikrofon fungerer! Signalnivå: {amplitude:.4f}")
                    self.root.after(0, lambda: self.update_status("Mikrofon OK", False))
            else:
                self.log("Ingen data mottatt fra mikrofonen!")
                self.root.after(0, lambda: self.update_status("Mikrofonfeil!", False))
        
        except Exception as e:
            self.log(f"Feil ved testing av mikrofon: {e}")
            self.root.after(0, lambda: self.update_status("Mikrofonfeil!", False))
        
        # Tilbakestill status etter 2 sekunder
        self.root.after(2000, lambda: self.update_status("Klar", False))

    def update_gain_label(self, *args):
        """Oppdater etiketten for følsomhet"""
        value = self.gain_var.get()
        self.gain_label.config(text=f"{value:.1f}x")

def main():
    """Hovedfunksjon som starter applikasjonen"""
    global app
    
    # Opprett hovedvinduet
    root = tk.Tk()
    app = TaleApp(root)
    
    # Last inn whisper-modellen i en bakgrunnstråd
    threading.Thread(target=load_whisper_model, daemon=True).start()
    
    # Registrer tastaturhendelser
    setup_keyboard_hooks()
    
    # Start hovedløkken
    root.mainloop()

def setup_keyboard_hooks():
    """Sett opp tastatursnarveier"""
    # Registrer hendelser for når snarveien trykkes og slippes
    keyboard.on_press_key(SHORTCUT.split('+')[-1], on_shortcut_press, suppress=True)
    keyboard.on_release_key(SHORTCUT.split('+')[-1], on_shortcut_release, suppress=True)

def on_shortcut_press(event):
    """Håndterer når snarveien trykkes"""
    # Sjekk at alle modifikatorer (Ctrl, Alt, osv.) er trykket
    if all(keyboard.is_pressed(key) for key in SHORTCUT.split('+')):
        start_recording()

def on_shortcut_release(event):
    """Håndterer når snarveien slippes"""
    global recording
    if recording:
        stop_recording()

def start_recording():
    """Start lydopptak når snarveien trykkes"""
    global recording, recording_data, app, model_loaded
    
    # Sjekk om modellen er lastet
    if not model_loaded:
        app.root.after(0, lambda: app.log("Kan ikke starte opptak: Whisper-modellen lastes fortsatt..."))
        app.root.after(0, lambda: app.update_status("Venter på modell", False))
        return
    
    if recording:
        return  # Allerede i opptak
    
    recording = True
    recording_data = []
    
    # Oppdater GUI i hovedtråden
    app.root.after(0, lambda: app.set_recording(True))
    
    # Start opptak i separat tråd
    threading.Thread(target=record_audio, daemon=True).start()

def stop_recording():
    """Stopp lydopptak når snarveien slippes og start transkripsjon"""
    global recording, recording_data, app
    
    if not recording:
        return  # Ikke i opptak
    
    recording = False
    
    # Oppdater GUI i hovedtråden
    app.root.after(0, lambda: app.set_recording(False))
    
    # Konverter opptaksdata til NumPy-array
    if recording_data:
        audio_data = np.concatenate(recording_data)
        
        # Lagre til midlertidig fil
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            import wave
            with wave.open(temp.name, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(app.device_sample_rate)
                wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
            
            # Logg informasjon om lydopptaket
            seconds = len(audio_data) / app.device_sample_rate
            app.root.after(0, lambda: app.log(f"Lydopptak ferdig: {seconds:.1f} sekunder med {app.device_sample_rate} Hz"))
            
            # Start transkripsjon i separat tråd
            threading.Thread(target=transcribe_audio, args=(temp.name,), daemon=True).start()
    else:
        app.root.after(0, lambda: app.log("Ingen lyd registrert"))
        app.root.after(0, lambda: app.update_status("Klar", False))
        app.root.after(0, lambda: app.stop_progress())

def record_audio():
    """Funksjon for å ta opp lyd"""
    global recording, recording_data, app
    
    def audio_callback(indata, frames, time, status):
        """Callback for lydopptak"""
        if recording:
            # Bruk gain-faktoren for å justere lydfølsomheten
            gain = app.gain_var.get()
            recording_data.append(indata.copy() * gain)
    
    # Start lydstrøm med den valgte mikrofonen og korrekt sample rate
    with sd.InputStream(samplerate=app.device_sample_rate, channels=CHANNELS, 
                      device=app.selected_device, callback=audio_callback):
        while recording:
            time.sleep(0.1)  # Reduser CPU-bruk

def load_whisper_model():
    """Last inn Whisper-modellen"""
    global whisper_model, app, model_loaded
    
    # Oppdater GUI i hovedtråden
    app.root.after(0, lambda: app.log("Laster inn Whisper-modellen..."))
    app.root.after(0, lambda: app.update_status("Laster modell...", False))
    app.root.after(0, lambda: app.update_model_status(False))
    
    try:
        # Vis detaljert informasjon om modellen som lastes
        app.root.after(0, lambda: app.log("Laster faster-whisper modell (large-v2)..."))
        app.root.after(0, lambda: app.log("Dette kan ta litt tid. Vennligst vent."))
        
        # Sett opp med detaljerte konfigurasjonsmuligheter
        whisper_model = WhisperModel(
            "large-v2",         # Bruk large-v2 modellen som er stabil på CPU
            device="cpu",       # Eksplisitt CPU
            compute_type="int8", # Bruk int8 kvantisering for CPU
            cpu_threads=4,       # Begrens til 4 tråder
            num_workers=1        # Bare bruk 1 arbeider
        )
        
        # Test modellen med en tom lydfil for å verifisere at den fungerer
        app.root.after(0, lambda: app.log("Tester modellen..."))
        
        # Opprett en tom testlydfil (1 sekund av stillhet)
        test_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        create_test_audio_file(test_file)
        
        # Test transkripsjon
        try:
            segments, _ = whisper_model.transcribe(test_file, language="no")
            # Konsumer segmentene for å faktisk kjøre transkripsjonen
            list(segments)
            app.root.after(0, lambda: app.log("Modelltest vellykket!"))
        except Exception as test_error:
            app.root.after(0, lambda: app.log(f"Modelltest feilet: {test_error}"))
            # Vi fortsetter likevel, siden hovedproblemet kan være med testfilen
        
        # Fjern testfilen
        try:
            os.unlink(test_file)
        except:
            pass
        
        # Merk at modellen er lastet
        model_loaded = True
        
        # Oppdater GUI i hovedtråden
        app.root.after(0, lambda: app.log("Whisper-modell lastet og klar til bruk"))
        app.root.after(0, lambda: app.update_status("Klar", False))
        app.root.after(0, lambda: app.update_model_status(True))
    except Exception as e:
        # Oppdater GUI i hovedtråden med detaljert feilmelding
        app.root.after(0, lambda: app.log(f"Feil ved lasting av Whisper-modell: {e}"))
        app.root.after(0, lambda: app.log(f"Feiltype: {type(e).__name__}"))
        app.root.after(0, lambda: app.log(f"Sjekk at du har nok minne og diskplass."))
        app.root.after(0, lambda: app.update_model_status(False, error=True))
        # Ikke avslutt, men sett modellen til ikke-lastet
        model_loaded = False

def create_test_audio_file(filename, duration=1.0, sample_rate=16000):
    """Opprett en testlydfil med stillhet"""
    try:
        # Generer 1 sekund stillhet (litt støy for å gjøre det realistisk)
        samples = np.random.randn(int(duration * sample_rate)) * 0.01
        
        # Skriv til WAV-fil
        import wave
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes((samples * 32767).astype(np.int16).tobytes())
        
        return True
    except Exception as e:
        app.root.after(0, lambda: app.log(f"Feil ved oppretting av testlydfil: {e}"))
        return False

def transcribe_audio(audio_file):
    """Transkriber lydfil med Whisper-modellen"""
    global whisper_model, temp_file, app
    
    # Lagre referanse til midlertidig fil for opprydding senere
    temp_file = audio_file
    
    try:
        # Resample lydfilen til 16kHz hvis nødvendig
        if app.device_sample_rate != 16000:
            app.root.after(0, lambda: app.log(f"Resampler fra {app.device_sample_rate}Hz til 16000Hz for transkripsjon..."))
            resampled_file = resample_audio(audio_file, app.device_sample_rate, 16000)
            if resampled_file:
                audio_file = resampled_file
                app.root.after(0, lambda: app.log("Resampling fullført"))
                app.root.after(0, lambda: app.log(f"Resamplet fil lagret som: {resampled_file}"))
        
        # Sjekk filstørrelse (for debugging)
        file_size = os.path.getsize(audio_file) / 1024  # KB
        app.root.after(0, lambda: app.log(f"Lydfil størrelse: {file_size:.1f} KB"))
        
        # Utfør transkripsjon med norsk som språk
        app.root.after(0, lambda: app.log("Starter transkripsjon med faster-whisper..."))
        
        # Detaljerte transkripsjonssettinger
        segments, info = whisper_model.transcribe(
            audio_file, 
            language="no",
            beam_size=1,         # Reduser beam size for raskere transkripsjon
            word_timestamps=False, # Ikke generer ord-timestamps
            vad_filter=True,     # Bruk VAD-filter for å fjerne stillhet
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # Logg info om transkripsjonen
        app.root.after(0, lambda: app.log(f"Transkripsjon fullført, behandler segmenter..."))
        
        # Samle alle segmenter til en sammenhengende tekst
        segments_list = list(segments)  # Konsumer segmentene
        app.root.after(0, lambda: app.log(f"Antall segmenter: {len(segments_list)}"))
        
        text = " ".join([segment.text for segment in segments_list])
        
        # Rydd opp og fjern ekstra mellomrom
        text = text.strip()
        
        if text:
            # Kopier tekst til utklippstavlen
            pyperclip.copy(text)
            
            # Oppdater GUI i hovedtråden
            app.root.after(0, lambda: app.show_transcription(text))
            app.root.after(0, lambda: app.log("Tekst kopiert til utklippstavlen"))
            
            # Lim inn tekst
            keyboard.press_and_release('ctrl+v')
            app.root.after(0, lambda: app.log("Tekst limt inn"))
        else:
            app.root.after(0, lambda: app.log("Ingen tekst ble generert fra opptaket"))
            app.root.after(0, lambda: app.update_status("Klar", False))
            
    except Exception as e:
        app.root.after(0, lambda: app.log(f"Feil under transkripsjon: {e}"))
        app.root.after(0, lambda: app.log(f"Feiltype: {type(e).__name__}"))
        
        # Prøv å vise mer informasjon om feilen
        import traceback
        error_details = traceback.format_exc()
        app.root.after(0, lambda: app.log(f"Detaljer: {error_details.splitlines()[-1]}"))
        
        app.root.after(0, lambda: app.update_status("Klar", False))
    finally:
        # Stopp fremdriftsindikator
        app.root.after(0, lambda: app.stop_progress())
        # Rydd opp midlertidig fil
        cleanup()
        # Rydd opp resampled fil hvis den finnes
        if 'resampled_file' in locals() and resampled_file and os.path.exists(resampled_file):
            try:
                os.unlink(resampled_file)
                app.root.after(0, lambda: app.log("Resamplet fil slettet"))
            except:
                pass

def resample_audio(input_file, orig_sr, target_sr):
    """Resample en lydfil til en ny sample rate"""
    try:
        # Les inn lydfilen
        import wave
        with wave.open(input_file, 'rb') as wf:
            # Hent innstillinger
            channels = wf.getnchannels()
            width = wf.getsampwidth()
            frames = wf.readframes(wf.getnframes())
        
        # Konverter til numpy array
        audio_data = np.frombuffer(frames, dtype=np.int16)
        audio_data = audio_data.astype(np.float32) / 32767.0
        
        if channels == 2:  # Stereo til mono
            audio_data = audio_data.reshape(-1, 2).mean(axis=1)
        
        # Resample
        number_of_samples = round(len(audio_data) * target_sr / orig_sr)
        audio_resampled = signal.resample(audio_data, number_of_samples)
        
        # Konverter tilbake til int16
        audio_resampled = (audio_resampled * 32767).astype(np.int16)
        
        # Skriv til ny fil
        output_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(1)  # Alltid mono for Whisper
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(target_sr)
            wf.writeframes(audio_resampled.tobytes())
        
        return output_file
    except Exception as e:
        app.root.after(0, lambda: app.log(f"Feil ved resampling: {e}"))
        return None

def cleanup():
    """Rydd opp midlertidige filer"""
    global temp_file, app
    
    if temp_file and os.path.exists(temp_file):
        try:
            os.unlink(temp_file)
            app.root.after(0, lambda: app.log(f"Midlertidig fil slettet"))
            temp_file = None
        except Exception as e:
            app.root.after(0, lambda: app.log(f"Feil ved sletting av midlertidig fil: {e}"))

if __name__ == "__main__":
    main() 