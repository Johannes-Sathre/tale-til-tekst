#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Transkriberingsmodul

Håndterer lasting av Whisper-modellen og transkripsjon av lyd til tekst.
"""

import os
import tempfile
import traceback
import numpy as np
import pyperclip
import keyboard
from scipy import signal
from faster_whisper import WhisperModel

# Globale variabler
whisper_model = None
model_loaded = False

def is_model_loaded():
    """Sjekk om modellen er lastet"""
    global model_loaded
    return model_loaded

def load_whisper_model(app):
    """Last inn Whisper-modellen"""
    global whisper_model, model_loaded
    
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
    except Exception:
        return False

def transcribe_audio(audio_file, app):
    """Transkriber lydfil med Whisper-modellen"""
    global whisper_model
    
    # Lagre referanse til midlertidig fil for opprydding senere
    from recorder import temp_file  # Importer globale variabler fra recorder
    
    try:
        # Resample lydfilen til 16kHz hvis nødvendig
        if app.device_sample_rate != 16000:
            app.root.after(0, lambda: app.log(f"Resampler fra {app.device_sample_rate}Hz til 16000Hz for transkripsjon..."))
            resampled_file = resample_audio(audio_file, app.device_sample_rate, 16000, app)
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
        error_details = traceback.format_exc()
        app.root.after(0, lambda: app.log(f"Detaljer: {error_details.splitlines()[-1]}"))
        
        app.root.after(0, lambda: app.update_status("Klar", False))
    finally:
        # Stopp fremdriftsindikator
        app.root.after(0, lambda: app.stop_progress())
        
        # Rydd opp midlertidig fil
        from recorder import cleanup
        cleanup()
        
        # Rydd opp resampled fil hvis den finnes
        if 'resampled_file' in locals() and resampled_file and os.path.exists(resampled_file):
            try:
                os.unlink(resampled_file)
                app.root.after(0, lambda: app.log("Resamplet fil slettet"))
            except:
                pass

def resample_audio(input_file, orig_sr, target_sr, app):
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