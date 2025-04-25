#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Opptaksmodul

Håndterer lydopptak og tastatursnarveier.
"""

import threading
import tempfile
import time
import numpy as np
import sounddevice as sd
import keyboard
import os

# Konstanter
CHANNELS = 1  # Mono
TEST_DURATION = 3  # 3 sekunder test

# Globale variabler
recording = False
recording_data = []
temp_file = None

def setup_keyboard_hooks(shortcut, app):
    """Sett opp tastatursnarveier"""
    # Registrer hendelser for når snarveien trykkes og slippes
    keyboard.on_press_key(shortcut.split('+')[-1], 
                         lambda e: on_shortcut_press(e, shortcut, app), 
                         suppress=True)
    keyboard.on_release_key(shortcut.split('+')[-1], 
                           lambda e: on_shortcut_release(e, app), 
                           suppress=True)
    
    # Sett opp mikrofon-testfunksjon for app
    app.run_mic_test_callback = lambda: run_mic_test(app)

def on_shortcut_press(event, shortcut, app):
    """Håndterer når snarveien trykkes"""
    # Sjekk at alle modifikatorer (Ctrl, Alt, osv.) er trykket
    if all(keyboard.is_pressed(key) for key in shortcut.split('+')):
        start_recording(app)

def on_shortcut_release(event, app):
    """Håndterer når snarveien slippes"""
    global recording
    if recording:
        stop_recording(app)

def start_recording(app):
    """Start lydopptak når snarveien trykkes"""
    global recording, recording_data
    
    # Sjekk om modellen er lastet
    from transcriber import is_model_loaded
    if not is_model_loaded():
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
    threading.Thread(target=lambda: record_audio(app), daemon=True).start()

def stop_recording(app):
    """Stopp lydopptak når snarveien slippes og start transkripsjon"""
    global recording, recording_data
    
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
            from transcriber import transcribe_audio
            threading.Thread(target=lambda: transcribe_audio(temp.name, app), daemon=True).start()
    else:
        app.root.after(0, lambda: app.log("Ingen lyd registrert"))
        app.root.after(0, lambda: app.update_status("Klar", False))
        app.root.after(0, lambda: app.stop_progress())

def record_audio(app):
    """Funksjon for å ta opp lyd"""
    global recording, recording_data
    
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

def run_mic_test(app):
    """Kjør en test av mikrofonen"""
    # Sjekk om modellen er lastet
    from transcriber import is_model_loaded
    if not is_model_loaded():
        app.log("Kan ikke teste mikrofon: Venter på at modellen lastes")
        return
        
    test_data = []
    
    def test_callback(indata, frames, time, status):
        test_data.append(indata.copy())
    
    try:
        # Start et kort opptak med riktig sample rate
        with sd.InputStream(samplerate=app.device_sample_rate, channels=CHANNELS, 
                         device=app.selected_device, callback=test_callback):
            # Vis nedtelling
            for i in range(TEST_DURATION, 0, -1):
                app.root.after(0, lambda i=i: app.update_status(f"Tester mikrofon... {i}", False))
                time.sleep(1)
        
        # Sjekk om vi fikk noe data
        if test_data:
            # Beregn lydnivå (amplitude)
            audio_data = np.concatenate(test_data)
            amplitude = np.abs(audio_data).mean() * 100
            
            if amplitude < 0.01:
                app.log(f"Advarsel: Veldig lavt lydnivå ({amplitude:.4f}). Sjekk at mikrofonen fungerer.")
                app.root.after(0, lambda: app.update_status("Mikrofon OK, men lavt signal", False))
            else:
                app.log(f"Mikrofon fungerer! Signalnivå: {amplitude:.4f}")
                app.root.after(0, lambda: app.update_status("Mikrofon OK", False))
        else:
            app.log("Ingen data mottatt fra mikrofonen!")
            app.root.after(0, lambda: app.update_status("Mikrofonfeil!", False))
    
    except Exception as e:
        app.log(f"Feil ved testing av mikrofon: {e}")
        app.root.after(0, lambda: app.update_status("Mikrofonfeil!", False))
    
    # Tilbakestill status etter 2 sekunder
    app.root.after(2000, lambda: app.update_status("Klar", False))

def cleanup():
    """Rydd opp midlertidige filer"""
    global temp_file
    
    if temp_file and os.path.exists(temp_file):
        try:
            os.unlink(temp_file)
            temp_file = None
            return True
        except Exception:
            return False
    return True 