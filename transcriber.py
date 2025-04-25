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
import requests
import json

# Importer fra vår egen moduler
from config import (
    AVAILABLE_WHISPER_MODELS, WHISPER_MODEL, WHISPER_COMPUTE_TYPE, 
    WHISPER_CPU_THREADS, WHISPER_NUM_WORKERS, configure_cpu_parameters, get_model_info,
    SAMPLE_RATE, OPENAI_API_KEY, OPENAI_MODEL, OPENAI_CORRECTION_PROMPT
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
        from config import WHISPER_MODEL
        
        # Hvis modellnavn er gitt, oppdater config først
        if model_name:
            configure_cpu_parameters(model_name)
            self.current_model = model_name
        else:
            # Ellers bruk gjeldende konfigurasjon
            self.current_model = WHISPER_MODEL
        
        # Oppdater GUI om status
        if self.app:
            self.app.update_model_status(loaded=False, error=False)
        
        try:
            print(f"Laster Whisper-modell '{self.current_model}'...")
            print(f"CPU-tråder: {WHISPER_CPU_THREADS}, Arbeidere: {WHISPER_NUM_WORKERS}")
            
            # Last inn modellen med gitte parametre
            self.model = WhisperModel(
                self.current_model,
                device="cpu",
                compute_type=WHISPER_COMPUTE_TYPE,
                cpu_threads=WHISPER_CPU_THREADS,
                num_workers=WHISPER_NUM_WORKERS
            )
            
            self.is_loaded = True
            print(f"Whisper-modell '{self.current_model}' lastet!")
            
            # Oppdater GUI om at modellen er lastet
            if self.app:
                self.app.update_model_status(loaded=True, error=False)
            
            return True
            
        except Exception as e:
            error_msg = f"Feil ved lasting av Whisper-modell: {e}"
            print(error_msg)
            traceback.print_exc()
            
            self.is_loaded = False
            self.model = None
            
            # Oppdater GUI om feil
            if self.app:
                self.app.update_model_status(loaded=False, error=True)
                self.app.log(error_msg)
            
            return False
    
    def transcribe_file(self, audio_file):
        """Transkriber en lydfil"""
        if not self.is_loaded or not self.model:
            error_msg = "Whisper-modell ikke lastet!"
            print(error_msg)
            
            if self.app:
                self.app.log(error_msg)
            
            return ""
        
        try:
            print(f"Transkriberer fil: {audio_file}")
            
            # Utfør transkribering med språkdeteksjon
            segments, info = self.model.transcribe(
                audio_file,
                beam_size=5,
                language="no",
                task="transcribe",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            
            # Samle segmentene
            result = ""
            for segment in segments:
                result += segment.text + " "
            
            result = result.strip()
            print(f"Transkripsjon fullført! Språk: {info.language}, Sannsynlighet: {info.language_probability:.2f}")
            print(f"Resultat ({len(result)} tegn): {result[:100]}...")
            
            # Oppdater GUI med transkripsjonen
            if self.app:
                self.app.add_transcription(result, is_final=False)
            
            # Bruk OpenAI for å korrigere hvis aktivert
            use_openai = False
            
            if self.app and hasattr(self.app, 'openai_check'):
                use_openai = self.app.openai_check.isChecked()
            
            if use_openai and OPENAI_API_KEY and result:
                print("Sender til OpenAI for korrigering...")
                
                try:
                    corrected = self.correct_with_openai(result)
                    if corrected:
                        print(f"OpenAI-korrigert resultat: {corrected[:100]}...")
                        
                        # Oppdater GUI med den korrigerte transkripsjonen
                        if self.app:
                            self.app.add_transcription(corrected, is_final=True, openai_corrected=True)
                        return corrected
                except Exception as e:
                    error_msg = f"Feil ved OpenAI-korrigering: {e}"
                    print(error_msg)
                    if self.app:
                        self.app.log(error_msg)
            
            # Oppdater GUI med endelig transkripsjon
            if self.app:
                self.app.add_transcription(result, is_final=True)
            
            return result
            
        except Exception as e:
            error_msg = f"Feil ved transkribering: {e}"
            print(error_msg)
            traceback.print_exc()
            
            if self.app:
                self.app.log(error_msg)
            
            return ""
    
    def correct_with_openai(self, text):
        """Korriger en transkripsjon med OpenAI API"""
        if not OPENAI_API_KEY:
            return None
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }
            
            payload = {
                "model": OPENAI_MODEL,
                "messages": [
                    {"role": "system", "content": OPENAI_CORRECTION_PROMPT},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.3,
                "max_tokens": 1024
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                result = response.json()
                corrected_text = result["choices"][0]["message"]["content"].strip()
                return corrected_text
            else:
                error_msg = f"Feil fra OpenAI API: {response.status_code} - {response.text}"
                print(error_msg)
                if self.app:
                    self.app.log(error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Feil ved OpenAI-korrigering: {e}"
            print(error_msg)
            if self.app:
                self.app.log(error_msg)
            return None
    
    def transcribe_audio_data(self, audio_data, sample_rate=SAMPLE_RATE):
        """Transkriber lyddata direkte"""
        if not self.is_loaded or not self.model:
            return ""
        
        try:
            # Skriv data til en midlertidig fil
            fd, temp_path = tempfile.mkstemp(suffix='.wav')
            os.close(fd)
            
            try:
                # Normaliser og konverter til int16
                max_val = np.max(np.abs(audio_data))
                if max_val > 0:
                    audio_data = audio_data / max_val * 32767
                audio_data = audio_data.astype(np.int16)
                
                # Skriv til WAV-fil
                from scipy.io import wavfile
                wavfile.write(temp_path, sample_rate, audio_data)
                
                # Transkriber filen
                return self.transcribe_file(temp_path)
                
            finally:
                # Rydd opp
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        except Exception as e:
            print(f"Feil ved transkribering av lyddata: {e}")
            traceback.print_exc()
            return "" 