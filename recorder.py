#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Opptaksmodul

Håndterer opptak av lyd fra mikrofon og leverer lyddata til transkribering.
"""

import os
import time
import tempfile
import threading
import queue
import numpy as np
import sounddevice as sd
import keyboard
from scipy.io import wavfile

# Importer fra våre egne moduler
from config import SAMPLE_RATE, CHANNELS, SUPPORTED_RATES, TEST_DURATION
from utils import create_test_audio_file

class Recorder:
    def __init__(self, transcriber):
        self.transcriber = transcriber
        self.recording = False
        self.app = None  # Referanse til GUI-app
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.keyboard_thread = None
        self.recording_data = []
        self.recorded_file = None
        self.shortcut_pressed = False
        self.sensitivity = 1.0  # Standardfølsomhet
        
        # Hent standard innspillingsenhet
        self.default_input_device = self._get_default_device()
        
        # Maksimal opptakstid i sekunder, 0 = ingen grense
        self.max_recording_time = 60
        
        # Vis enhetsinformasjon ved oppstart
        self.print_device_info()
    
    def _get_default_device(self):
        """Hent standard lydopptaksenhet"""
        try:
            return sd.default.device[0]
        except:
            return None
    
    def set_app(self, app):
        """Setter referanse til applikasjonen"""
        self.app = app
    
    def print_device_info(self):
        """Skriv ut informasjon om tilgjengelige lydenheter"""
        try:
            devices = sd.query_devices()
            default_device = sd.default.device
            
            print("\nTilgjengelige lydopptaksenheter:")
            print("-" * 50)
            
            for i, device in enumerate(devices):
                is_input = device['max_input_channels'] > 0
                is_default = i == default_device[0] if isinstance(default_device, tuple) else i == default_device
                
                if is_input:
                    default_mark = " (standard)" if is_default else ""
                    print(f"[{i}] {device['name']}{default_mark}")
                    print(f"    Kanaler: {device['max_input_channels']}")
                    print(f"    Samplingsfrekvenser: {device['default_samplerate']} Hz")
                    print()
            
            print("-" * 50)
        except Exception as e:
            print(f"Kunne ikke hente enhetsinformasjon: {e}")
    
    def setup_keyboard_hooks(self, shortcut):
        """Sett opp lytting etter tastatursnarvei"""
        keyboard.on_press_key(shortcut.split('+')[-1], self._on_shortcut_press, suppress=False)
        keyboard.on_release_key(shortcut.split('+')[-1], self._on_shortcut_release, suppress=False)
    
    def _on_shortcut_press(self, e):
        """Håndter start av opptak når tastatursnarvei trykkes"""
        # Sjekk om alle modifikasjonstaster er trykket
        shortcut_parts = e.name.split('+')
        
        # For ctrl+alt+s, sjekk at både ctrl og alt er trykket
        if ('ctrl' in shortcut_parts or keyboard.is_pressed('ctrl')) and \
           ('alt' in shortcut_parts or keyboard.is_pressed('alt')):
            if not self.shortcut_pressed:
                self.shortcut_pressed = True
                self.start_recording()
    
    def _on_shortcut_release(self, e):
        """Håndter stopp av opptak når tastatursnarvei slippes"""
        if self.shortcut_pressed:
            self.shortcut_pressed = False
            self.stop_recording()
    
    def get_devices(self):
        """Hent liste over tilgjengelige mikrofoner"""
        devices = []
        try:
            all_devices = sd.query_devices()
            for i, device in enumerate(all_devices):
                if device['max_input_channels'] > 0:
                    devices.append({
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate']
                    })
        except Exception as e:
            print(f"Feil ved henting av lydenheter: {e}")
        
        return devices
    
    def start_recording(self, device_id=None):
        """Start opptak fra valgt enhet"""
        if self.recording:
            return
        
        # Bruk valgt enhet eller standard
        device = device_id if device_id is not None else self.default_input_device
        
        try:
            # Tilbakestill datastruktur for nye opptak
            self.recording_data = []
            
            # Vis opptaksstatus i GUI
            if self.app:
                self.app.update_recording_status(True)
            
            # Start opptakstråd
            self.recording = True
            self.recording_thread = threading.Thread(
                target=self._recording_thread,
                args=(device,),
                daemon=True
            )
            self.recording_thread.start()
            
        except Exception as e:
            print(f"Feil ved start av opptak: {e}")
            if self.app:
                self.app.update_recording_status(False)
            self.recording = False
    
    def stop_recording(self):
        """Stopp pågående opptak"""
        if not self.recording:
            return
        
        self.recording = False
        
        # Vis opptaksstatus i GUI
        if self.app:
            self.app.update_recording_status(False)
        
        # Vent på at opptakstråden skal fullføre
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=1.0)
        
        # Lagre opptaket til en midlertidig fil
        self.save_recording()
        
        # Start transkribering
        if self.transcriber and hasattr(self.transcriber, 'transcribe_file'):
            # Opprett en transkripsjonstråd
            if self.app:
                self.app.update_transcribing_status(True)
            
            threading.Thread(
                target=self.transcribe_recording,
                daemon=True
            ).start()
    
    def _recording_thread(self, device):
        """Tråd for opptak av lyd"""
        try:
            def audio_callback(indata, frames, time, status):
                """Callback for lydstrøm"""
                if status:
                    print(f"Status: {status}")
                
                # Lagre dataene med følsomhetsjustering
                adjusted_data = indata.copy() * self.sensitivity
                self.recording_data.append(adjusted_data.copy())
                
                # Legg til i køen for visualisering
                try:
                    # Vi bruker bare første kanal for visualisering
                    self.audio_queue.put(adjusted_data[:, 0], block=False)
                except queue.Full:
                    pass
            
            # Start lydstrøm
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                device=device,
                channels=CHANNELS,
                callback=audio_callback
            ):
                start_time = time.time()
                
                # Fortsett til opptak stoppes eller maks tid nås
                while self.recording:
                    time.sleep(0.1)  # Reduser CPU-bruk
                    
                    # Stopp hvis maksimal opptakstid er nådd
                    if self.max_recording_time > 0 and time.time() - start_time > self.max_recording_time:
                        print(f"Maksimal opptakstid ({self.max_recording_time}s) nådd")
                        self.recording = False
                        
                        # Vis opptaksstatus i GUI fra hovedtråden
                        if self.app:
                            try:
                                import threading
                                if threading.current_thread() != threading.main_thread():
                                    from PyQt6.QtCore import QMetaObject, Qt, Q_ARG
                                    QMetaObject.invokeMethod(
                                        self.app, "update_recording_status", 
                                        Qt.ConnectionType.QueuedConnection,
                                        Q_ARG(bool, False)
                                    )
                            except ImportError:
                                # Fallback hvis ikke Qt
                                if hasattr(self.app, 'update_recording_status'):
                                    self.app.update_recording_status(False)
                        break
            
        except Exception as e:
            print(f"Feil under opptak: {e}")
            self.recording = False
            if self.app:
                self.app.update_recording_status(False)
    
    def save_recording(self):
        """Lagre opptaket til en lydfil"""
        if not self.recording_data:
            print("Ingen opptaksdata å lagre")
            return None
        
        try:
            # Kombiner alle bufre
            audio_data = np.vstack(self.recording_data)
            
            # Normaliser til 16-bit for WAV
            max_val = np.max(np.abs(audio_data))
            if max_val > 0:  # Unngå divisjon med null
                audio_data = audio_data / max_val * 32767
            
            # Konverter til 16-bit heltall
            audio_data = audio_data.astype(np.int16)
            
            # Opprett en midlertidig fil
            fd, temp_path = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            
            # Lagre til WAV-fil
            wavfile.write(temp_path, SAMPLE_RATE, audio_data)
            
            print(f"Opptak lagret til: {temp_path}")
            self.recorded_file = temp_path
            return temp_path
            
        except Exception as e:
            print(f"Feil ved lagring av opptak: {e}")
            return None
    
    def transcribe_recording(self):
        """Transkriber det siste opptaket"""
        if not self.recorded_file or not os.path.exists(self.recorded_file):
            print("Ingen opptaksfil tilgjengelig for transkribering")
            if self.app:
                self.app.update_transcribing_status(False)
            return
        
        try:
            # Start transkribering
            result = self.transcriber.transcribe_file(self.recorded_file)
            
            # Oppdater GUI
            if self.app:
                self.app.update_transcribing_status(False)
                if result:
                    self.app.add_transcription(result, is_final=True)
            
        except Exception as e:
            print(f"Feil ved transkribering: {e}")
            if self.app:
                self.app.update_transcribing_status(False)
    
    def set_sensitivity(self, value):
        """Sett mikrofonens følsomhet"""
        self.sensitivity = max(0.1, min(2.0, value))
        return self.sensitivity
    
    def get_audio_data(self):
        """Hent nyeste lyddata for visualisering"""
        try:
            return self.audio_queue.get_nowait()
        except queue.Empty:
            return None
    
    def test_microphone(self, device_id=None):
        """Test valgt mikrofon"""
        try:
            # Bruk valgt enhet eller standard
            device = device_id if device_id is not None else self.default_input_device
            
            print(f"Tester mikrofon (enhet {device})...")
            
            # Opprett og spill av testfil
            test_file = create_test_audio_file()
            
            # Opptak av testlyd i TEST_DURATION sekunder
            test_recording = []
            
            def callback(indata, frames, time, status):
                if status:
                    print(f"Status: {status}")
                test_recording.append(indata.copy())
            
            # Start kortvarig opptak
            with sd.InputStream(samplerate=SAMPLE_RATE, device=device,
                              channels=CHANNELS, callback=callback):
                print(f"Opptak pågår i {TEST_DURATION} sekunder...")
                for i in range(TEST_DURATION):
                    time.sleep(1)
                    print(f"{i+1}/{TEST_DURATION}...")
            
            print("Mikrofon testet og fungerer!")
            
            # Logg til GUI
            if self.app:
                self.app.log("Mikrofon testet og fungerer!")
            
            return True
            
        except Exception as e:
            error_msg = f"Feil ved testing av mikrofon: {e}"
            print(error_msg)
            
            # Logg til GUI
            if self.app:
                self.app.log(error_msg)
            
            return False
    
    def cleanup(self):
        """Frigjør ressurser ved avslutning"""
        # Stopp eventuelt pågående opptak
        self.recording = False
        
        # Slett midlertidige filer
        if self.recorded_file and os.path.exists(self.recorded_file):
            try:
                os.unlink(self.recorded_file)
            except:
                pass 