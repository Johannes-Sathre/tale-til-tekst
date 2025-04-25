#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Opptaksmodul

Håndterer lydopptak og tastatursnarveier.
"""

import os
import threading
import tempfile
import time
import numpy as np
import sounddevice as sd
import keyboard
import pyperclip

# Import fra våre egne moduler
from config import CHANNELS, TEST_DURATION

class Recorder:
    def __init__(self, transcriber=None):
        self.transcriber = transcriber
        self.app = None  # Referanse til GUI-app
        self.recording = False
        self.recording_data = []
        self.temp_file = None
        self.shortcut = None
    
    def set_app(self, app):
        """Setter referanse til applikasjonen"""
        self.app = app
    
    def set_transcriber(self, transcriber):
        """Setter referanse til transkriberer"""
        self.transcriber = transcriber
    
    def setup_keyboard_hooks(self, shortcut):
        """Sett opp tastatursnarveier"""
        self.shortcut = shortcut
        
        # For å unngå å blokkere 's' når den brukes alene, bruker vi en annen tilnærming
        # Vi lytter på tastekombinasjon-hendelser i stedet for individuelle taster
        keyboard.add_hotkey(shortcut, self.start_recording, suppress=False, trigger_on_release=False)
        
        # For å detektere når snarveien slippes, sjekker vi når en av tastene i snarveien slippes
        for key in shortcut.split('+'):
            keyboard.on_release_key(key, self.check_recording_stop, suppress=False)
    
    def check_recording_stop(self, event):
        """Sjekk om vi skal stoppe opptak når en del av snarveien slippes"""
        if self.recording:
            self.stop_recording()
    
    def start_recording(self):
        """Start lydopptak når snarveien trykkes"""
        # Sjekk om modellen er lastet
        if not self.transcriber or not self.transcriber.is_model_loaded():
            if self.app:
                self.app.log("Kan ikke starte opptak: Whisper-modellen lastes fortsatt...")
                self.app.update_status("Venter på modell", False)
            return
        
        if self.recording:
            return  # Allerede i opptak
        
        self.recording = True
        self.recording_data = []
        
        # Oppdater GUI
        if self.app:
            self.app.set_recording(True)
        
        # Start opptak i separat tråd
        threading.Thread(target=self.record_audio, daemon=True).start()
    
    def stop_recording(self):
        """Stopp lydopptak når snarveien slippes og start transkripsjon"""
        if not self.recording:
            return  # Ikke i opptak
        
        self.recording = False
        
        # Oppdater GUI
        if self.app:
            self.app.set_recording(False)
        
        # Konverter opptaksdata til NumPy-array
        if self.recording_data and self.app:
            audio_data = np.concatenate(self.recording_data)
            
            # Lagre til midlertidig fil
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
                import wave
                with wave.open(temp.name, 'wb') as wf:
                    wf.setnchannels(CHANNELS)
                    wf.setsampwidth(2)  # 16-bit
                    wf.setframerate(self.app.device_sample_rate)
                    wf.writeframes((audio_data * 32767).astype(np.int16).tobytes())
                
                # Lagre filnavnet for senere opprydding
                self.temp_file = temp.name
                
                # Logg informasjon om lydopptaket
                seconds = len(audio_data) / self.app.device_sample_rate
                self.app.log(f"Lydopptak ferdig: {seconds:.1f} sekunder med {self.app.device_sample_rate} Hz")
                
                # Start transkripsjon i separat tråd
                threading.Thread(target=self.process_recording, args=(temp.name,), daemon=True).start()
        else:
            if self.app:
                self.app.log("Ingen lyd registrert")
                self.app.update_status("Klar", False)
                self.app.stop_progress()
    
    def process_recording(self, audio_file):
        """Behandle opptaket og transkriber"""
        if not self.transcriber or not self.app:
            return
        
        text = self.transcriber.transcribe(audio_file, self.app.device_sample_rate)
        
        if text:
            # Kopier tekst til utklippstavlen
            pyperclip.copy(text)
            
            # Oppdater GUI
            self.app.show_transcription(text)
            self.app.log("Tekst kopiert til utklippstavlen")
            
            # Lim inn tekst
            keyboard.press_and_release('ctrl+v')
            self.app.log("Tekst limt inn")
        else:
            self.app.log("Ingen tekst ble generert fra opptaket")
            self.app.update_status("Klar", False)
        
        # Stopp fremdriftsindikator
        self.app.stop_progress()
        
        # Rydd opp midlertidig fil
        self.cleanup()
    
    def record_audio(self):
        """Funksjon for å ta opp lyd"""
        if not self.app:
            return
        
        def audio_callback(indata, frames, time, status):
            """Callback for lydopptak"""
            if self.recording:
                # Bruk gain-faktoren for å justere lydfølsomheten
                gain = self.app.gain_var.get()
                self.recording_data.append(indata.copy() * gain)
        
        # Start lydstrøm med den valgte mikrofonen og korrekt sample rate
        with sd.InputStream(samplerate=self.app.device_sample_rate, channels=CHANNELS, 
                          device=self.app.selected_device, callback=audio_callback):
            while self.recording:
                time.sleep(0.1)  # Reduser CPU-bruk
    
    def test_microphone(self):
        """Kjør en test av mikrofonen"""
        if not self.app:
            return
            
        # Sjekk om modellen er lastet
        if self.transcriber and not self.transcriber.is_model_loaded():
            self.app.log("Kan ikke teste mikrofon: Venter på at modellen lastes")
            return
            
        test_data = []
        
        def test_callback(indata, frames, time, status):
            test_data.append(indata.copy())
        
        try:
            # Start et kort opptak med riktig sample rate
            with sd.InputStream(samplerate=self.app.device_sample_rate, channels=CHANNELS, 
                             device=self.app.selected_device, callback=test_callback):
                # Vis nedtelling
                for i in range(TEST_DURATION, 0, -1):
                    self.app.root.after(0, lambda i=i: self.app.update_status(f"Tester mikrofon... {i}", False))
                    time.sleep(1)
            
            # Sjekk om vi fikk noe data
            if test_data:
                # Beregn lydnivå (amplitude)
                audio_data = np.concatenate(test_data)
                amplitude = np.abs(audio_data).mean() * 100
                
                if amplitude < 0.01:
                    self.app.log(f"Advarsel: Veldig lavt lydnivå ({amplitude:.4f}). Sjekk at mikrofonen fungerer.")
                    self.app.root.after(0, lambda: self.app.update_status("Mikrofon OK, men lavt signal", False))
                else:
                    self.app.log(f"Mikrofon fungerer! Signalnivå: {amplitude:.4f}")
                    self.app.root.after(0, lambda: self.app.update_status("Mikrofon OK", False))
            else:
                self.app.log("Ingen data mottatt fra mikrofonen!")
                self.app.root.after(0, lambda: self.app.update_status("Mikrofonfeil!", False))
        
        except Exception as e:
            self.app.log(f"Feil ved testing av mikrofon: {e}")
            self.app.root.after(0, lambda: self.app.update_status("Mikrofonfeil!", False))
        
        # Tilbakestill status etter 2 sekunder
        self.app.root.after(2000, lambda: self.app.update_status("Klar", False))
    
    def cleanup(self):
        """Rydd opp midlertidige filer"""
        if self.temp_file and os.path.exists(self.temp_file):
            try:
                os.unlink(self.temp_file)
                if self.app:
                    self.app.log("Midlertidig fil slettet")
                self.temp_file = None
                return True
            except Exception as e:
                if self.app:
                    self.app.log(f"Feil ved sletting av midlertidig fil: {e}")
                return False
        return True 