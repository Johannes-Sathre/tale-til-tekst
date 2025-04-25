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
from scipy import signal
from faster_whisper import WhisperModel

# Importer fra vår egen moduler
from config import (
    AVAILABLE_WHISPER_MODELS, WHISPER_MODEL, WHISPER_COMPUTE_TYPE, 
    WHISPER_CPU_THREADS, WHISPER_NUM_WORKERS, configure_cpu_parameters, get_model_info,
    SAMPLE_RATE
)
from utils import create_test_audio_file

class Transcriber:
    def __init__(self):
        self.model = None
        self.is_loaded = False
        self.app = None  # Referanse til GUI-app
        self.current_model = WHISPER_MODEL
    
    def set_app(self, app):
        """Setter referanse til applikasjonen"""
        self.app = app
    
    def is_model_loaded(self):
        """Sjekk om modellen er lastet"""
        return self.is_loaded
    
    def get_current_model(self):
        """Returnerer gjeldende modellnavn"""
        return self.current_model
    
    def load_model(self, model_name=None):
        """Last inn Whisper-modellen"""
        # Bruk modellnavnet hvis angitt, ellers bruk gjeldende/standard
        if model_name and model_name in AVAILABLE_WHISPER_MODELS:
            # Oppdater CPU-parametre basert på ny modell
            configure_cpu_parameters(model_name)
            self.current_model = model_name
        
        if self.app:
            self.app.log(f"Laster inn Whisper-modellen ({self.current_model})...")
            self.app.update_status("Laster modell...", False)
            self.app.update_model_status(False)
            
            try:
                # Detaljert informasjon om modellen som lastes
                self.app.log(f"Laster faster-whisper modell ({self.current_model})...")
                self.app.log("Dette kan ta litt tid. Vennligst vent.")
                
                # Initialiser Whisper-modellen
                self.model = WhisperModel(
                    self.current_model,  
                    device="cpu",
                    compute_type=WHISPER_COMPUTE_TYPE,
                    cpu_threads=WHISPER_CPU_THREADS,
                    num_workers=WHISPER_NUM_WORKERS
                )
                
                # Test modellen med en tom lydfil
                self.app.log("Tester modellen...")
                test_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
                create_test_audio_file(test_file)
                
                try:
                    segments, _ = self.model.transcribe(test_file, language="no")
                    list(segments)  # Konsum segmentene
                    self.app.log("Modelltest vellykket!")
                except Exception as test_error:
                    self.app.log(f"Modelltest feilet: {test_error}")
                
                # Rydd opp testfil
                try:
                    os.unlink(test_file)
                except:
                    pass
                
                # Marker modellen som lastet
                self.is_loaded = True
                
                # Oppdater GUI
                self.app.log(f"Whisper-modell ({self.current_model}) lastet og klar til bruk")
                self.app.update_status("Klar", False)
                self.app.update_model_status(True)
            
            except Exception as e:
                # Logg feil
                self.app.log(f"Feil ved lasting av Whisper-modell: {e}")
                self.app.log(f"Feiltype: {type(e).__name__}")
                self.app.log(f"Sjekk at du har nok minne og diskplass.")
                self.app.update_model_status(False, error=True)
                self.is_loaded = False
    
    def transcribe(self, audio_file, device_sample_rate=SAMPLE_RATE):
        """Transkriber lydfil til tekst"""
        if not self.is_loaded or not self.app:
            return None
        
        try:
            # Resample lydfilen om nødvendig
            if device_sample_rate != SAMPLE_RATE:
                self.app.log(f"Resampler fra {device_sample_rate}Hz til {SAMPLE_RATE}Hz...")
                resampled_file = self.resample_audio(audio_file, device_sample_rate, SAMPLE_RATE)
                if resampled_file:
                    audio_file = resampled_file
                    self.app.log("Resampling fullført")
            
            # Sjekk filstørrelse
            file_size = os.path.getsize(audio_file) / 1024  # KB
            self.app.log(f"Lydfil størrelse: {file_size:.1f} KB")
            
            # Start transkripsjon
            self.app.log("Starter transkripsjon med faster-whisper...")
            
            segments, info = self.model.transcribe(
                audio_file, 
                language="no",
                beam_size=1,
                word_timestamps=False,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Behandle segmenter
            self.app.log("Transkripsjon fullført, behandler segmenter...")
            segments_list = list(segments)
            self.app.log(f"Antall segmenter: {len(segments_list)}")
            
            # Slå sammen segmentene
            text = " ".join([segment.text for segment in segments_list]).strip()
            
            # Rydd opp resampled fil hvis den finnes
            if 'resampled_file' in locals() and resampled_file and os.path.exists(resampled_file):
                try:
                    os.unlink(resampled_file)
                    self.app.log("Resamplet fil slettet")
                except:
                    pass
            
            return text
            
        except Exception as e:
            self.app.log(f"Feil under transkripsjon: {e}")
            self.app.log(f"Feiltype: {type(e).__name__}")
            
            # Vis mer informasjon om feilen
            error_details = traceback.format_exc()
            self.app.log(f"Detaljer: {error_details.splitlines()[-1]}")
            
            return None
    
    def resample_audio(self, input_file, orig_sr, target_sr):
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
                wf.setnchannels(1)  # Alltid mono
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(target_sr)
                wf.writeframes(audio_resampled.tobytes())
            
            return output_file
            
        except Exception as e:
            if self.app:
                self.app.log(f"Feil ved resampling: {e}")
            return None 