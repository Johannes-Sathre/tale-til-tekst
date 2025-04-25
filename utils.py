#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Verktøysmodul

Hjelpefunksjoner og verktøy for applikasjonen.
"""

import os
from io import BytesIO
from PIL import Image, ImageTk
from cairosvg import svg2png
import requests
import json
import difflib
import re

# Importer OpenAI API innstillinger
from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_CORRECTION_PROMPT

# Fargekoder for terminal
class TerminalColors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def save_svg_icon(svg_content, filename):
    """Lagre SVG-innhold til fil"""
    if not os.path.exists("resources/icons"):
        os.makedirs("resources/icons", exist_ok=True)
        
    filepath = os.path.join("resources/icons", filename)
    
    # Hvis filen allerede finnes, ikke skriv over
    if os.path.exists(filepath):
        return filepath
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)
        
    return filepath

def last_ikon(filnavn, størrelse=24):
    """Laster ikon fra SVG eller PNG-fil"""
    # Sjekk om filbanen er relativ
    if not os.path.isabs(filnavn):
        # Sjekk i resources/icons mappen
        if not filnavn.startswith("resources/"):
            ikon_fil = os.path.join("resources", "icons", filnavn)
        else:
            ikon_fil = filnavn
    else:
        ikon_fil = filnavn
        
    # Prøv å finne SVG-fil
    svg_fil = ikon_fil
    if not svg_fil.endswith(".svg"):
        svg_fil = f"{ikon_fil}.svg"
    
    # Prøv å finne PNG-fil
    png_fil = ikon_fil
    if not png_fil.endswith(".png"):
        png_fil = f"{ikon_fil}.png"
        
    try:
        # Først prøv SVG
        if os.path.exists(svg_fil):
            # Konverter SVG til PIL-image
            png_data = BytesIO()
            with open(svg_fil, 'rb') as svg_file:
                svg_data = svg_file.read()
                svg2png(bytestring=svg_data, write_to=png_data, 
                        output_width=størrelse, output_height=størrelse)
            png_data.seek(0)
            return ImageTk.PhotoImage(Image.open(png_data))
        
        # Så prøv PNG
        elif os.path.exists(png_fil):
            img = Image.open(png_fil)
            if img.width != størrelse or img.height != størrelse:
                img = img.resize((størrelse, størrelse), Image.LANCZOS)
            return ImageTk.PhotoImage(img)
            
    except Exception as e:
        print(f"Feil ved lasting av ikon {filnavn}: {e}")
    
    return None

def setup_icons(icons_dict):
    """Sett opp standard ikoner for applikasjonen"""
    # Lagre standardikoner
    for name, svg_content in icons_dict.items():
        save_svg_icon(svg_content, f"{name}.svg")
        
def create_test_audio_file(filename, duration=1.0, sample_rate=16000):
    """Opprett en testlydfil med stillhet"""
    try:
        import numpy as np
        import wave
        
        # Generer stillhet med litt støy
        samples = np.random.randn(int(duration * sample_rate)) * 0.01
        
        # Skriv til WAV-fil
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(1)  # Mono
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(sample_rate)
            wf.writeframes((samples * 32767).astype(np.int16).tobytes())
        
        return True
    except Exception as e:
        print(f"Feil ved oppretting av testlydfil: {e}")
        return False

def show_word_diff(original, corrected):
    """
    Viser forskjeller mellom to tekster på ordnivå med farger.
    
    Args:
        original (str): Original tekst
        corrected (str): Korrigert tekst
    """
    # Del opp teksten i ord
    original_words = re.findall(r'\S+|\s+', original)
    corrected_words = re.findall(r'\S+|\s+', corrected)
    
    # Bruk difflib for å finne forskjellene
    matcher = difflib.SequenceMatcher(None, original_words, corrected_words)
    
    print(f"\n{TerminalColors.BOLD}=== DETALJERT ORD-FOR-ORD SAMMENLIGNING ==={TerminalColors.END}")
    print(f"{TerminalColors.RED}RØDT{TerminalColors.END}: Fjernet   {TerminalColors.GREEN}GRØNT{TerminalColors.END}: Lagt til   {TerminalColors.YELLOW}GULT{TerminalColors.END}: Erstattet")
    
    # For å formatere resultatene i pene linjer
    line_length = 0
    max_line_length = 80
    result_lines = []
    current_line = ""
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # Uendrede ord - vis i vanlig tekst
            for word in original_words[i1:i2]:
                if line_length + len(word) > max_line_length and not word.isspace():
                    result_lines.append(current_line)
                    current_line = ""
                    line_length = 0
                
                current_line += word
                line_length += len(word)
                
        elif tag == 'delete':
            # Slettede ord - vis i rødt
            for word in original_words[i1:i2]:
                if not word.isspace():  # Ignorer mellomrom ved beregning av linjelengde
                    colored_word = f"{TerminalColors.RED}{word}{TerminalColors.END}"
                    if line_length + len(word) > max_line_length:
                        result_lines.append(current_line)
                        current_line = ""
                        line_length = 0
                    
                    current_line += colored_word
                    line_length += len(word)
                else:
                    current_line += word
                    line_length += len(word)
                
        elif tag == 'insert':
            # Nye ord - vis i grønt
            for word in corrected_words[j1:j2]:
                if not word.isspace():  # Ignorer mellomrom ved beregning av linjelengde
                    colored_word = f"{TerminalColors.GREEN}{word}{TerminalColors.END}"
                    if line_length + len(word) > max_line_length:
                        result_lines.append(current_line)
                        current_line = ""
                        line_length = 0
                    
                    current_line += colored_word
                    line_length += len(word)
                else:
                    current_line += word
                    line_length += len(word)
                
        elif tag == 'replace':
            # Endrede ord - fjernet (rød) og lagt til (grønn)
            # Først vis slettede ord
            for word in original_words[i1:i2]:
                if not word.isspace():
                    colored_word = f"{TerminalColors.YELLOW}{word}{TerminalColors.END}"
                    if line_length + len(word) > max_line_length:
                        result_lines.append(current_line)
                        current_line = ""
                        line_length = 0
                    
                    current_line += colored_word
                    line_length += len(word)
                else:
                    current_line += word
                    line_length += len(word)
            
            # Så vis nye ord
            for word in corrected_words[j1:j2]:
                if not word.isspace():
                    colored_word = f"{TerminalColors.GREEN}{word}{TerminalColors.END}"
                    if line_length + len(word) > max_line_length:
                        result_lines.append(current_line)
                        current_line = ""
                        line_length = 0
                    
                    current_line += colored_word
                    line_length += len(word)
                else:
                    current_line += word
                    line_length += len(word)
    
    # Legg til siste linje
    if current_line:
        result_lines.append(current_line)
    
    # Skriv ut alle linjene
    for line in result_lines:
        print(line)
    
    # Skriv ut sammendrag av endringer
    num_changes = sum(1 for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != 'equal')
    print(f"\n{TerminalColors.BOLD}Sammendrag:{TerminalColors.END} {num_changes} endringer oppdaget")

def show_sentence_diff(original, corrected):
    """
    Viser forskjeller mellom to tekster på setningsnivå.
    
    Args:
        original (str): Original tekst
        corrected (str): Korrigert tekst
    """
    # Del opp i setninger (enkel implementasjon)
    def split_into_sentences(text):
        # Enkelt mønster for å identifisere setninger
        # Dette kan være utilstrekkelig for kompleks tekst
        # Bedre setningssplitting kan oppnås med biblioteker som nltk
        return re.split(r'(?<=[.!?])\s+', text)
    
    original_sentences = split_into_sentences(original)
    corrected_sentences = split_into_sentences(corrected)
    
    # Sammenlign setninger
    matcher = difflib.SequenceMatcher(None, original_sentences, corrected_sentences)
    
    print(f"\n{TerminalColors.BOLD}=== SETNINGSSAMMENLIGNING ==={TerminalColors.END}")
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for sentence in original_sentences[i1:i2]:
                print(f"  {sentence}")
        elif tag == 'delete':
            for sentence in original_sentences[i1:i2]:
                print(f"- {TerminalColors.RED}{sentence}{TerminalColors.END}")
        elif tag == 'insert':
            for sentence in corrected_sentences[j1:j2]:
                print(f"+ {TerminalColors.GREEN}{sentence}{TerminalColors.END}")
        elif tag == 'replace':
            print(f"{TerminalColors.YELLOW}Endret fra:{TerminalColors.END}")
            for sentence in original_sentences[i1:i2]:
                print(f"- {TerminalColors.RED}{sentence}{TerminalColors.END}")
            print(f"{TerminalColors.YELLOW}Til:{TerminalColors.END}")
            for sentence in corrected_sentences[j1:j2]:
                print(f"+ {TerminalColors.GREEN}{sentence}{TerminalColors.END}")

def correct_text_with_openai(text, api_key=None, verbose=True):
    """
    Bruker OpenAI API til å korrigere transkriberte tekster.
    
    Args:
        text (str): Teksten som skal korrigeres
        api_key (str, optional): API-nøkkel for OpenAI, hvis ikke angitt brukes verdi fra config
        verbose (bool): Om detaljert utskrift skal vises i terminalen
        
    Returns:
        str: Korrigert tekst, eller None hvis korrigering feilet
    """
    if not text or text.strip() == "":
        return None
        
    # Bruk api_key hvis angitt, ellers bruk standard fra config
    api_key = api_key or OPENAI_API_KEY
    
    if not api_key:
        if verbose:
            print("Ingen API-nøkkel tilgjengelig for OpenAI")
        return None  # Ingen API-nøkkel tilgjengelig
    
    try:
        if verbose:
            print(f"\n{TerminalColors.BOLD}{TerminalColors.BLUE}=== ORIGINAL TRANSKRIPSJON ==={TerminalColors.END}")
            print(text)
            print(f"\n{TerminalColors.BOLD}{TerminalColors.BLUE}=== SENDER TIL OPENAI ==={TerminalColors.END}")
            print(f"System prompt: {OPENAI_CORRECTION_PROMPT}")
            print(f"Bruker modell: {OPENAI_MODEL}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": OPENAI_CORRECTION_PROMPT},
                {"role": "user", "content": text}
            ],
            "temperature": 0.3,  # Lavere temperatur for mer konservative endringer
            "max_tokens": 2000,  # Maksimalt antall tokens i svaret
        }
        
        if verbose:
            print(f"{TerminalColors.CYAN}Sender forespørsel til OpenAI...{TerminalColors.END}")
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload)
        )
        
        if response.status_code == 200:
            response_data = response.json()
            corrected_text = response_data["choices"][0]["message"]["content"].strip()
            
            if verbose:
                print(f"\n{TerminalColors.BOLD}{TerminalColors.BLUE}=== SVAR FRA OPENAI ==={TerminalColors.END}")
                print(corrected_text)
                
                # Vis endringer (forskjeller)
                if text == corrected_text:
                    print(f"\n{TerminalColors.BOLD}{TerminalColors.GREEN}=== INGEN ENDRINGER GJORT ==={TerminalColors.END}")
                else:
                    # Vis detaljerte forskjeller
                    show_word_diff(text, corrected_text)
                    show_sentence_diff(text, corrected_text)
                
                print(f"\n{TerminalColors.BOLD}{TerminalColors.BLUE}=== SLUTT PÅ OPENAI KORREKTUR ==={TerminalColors.END}")
            
            return corrected_text
        else:
            if verbose:
                print(f"\n{TerminalColors.BOLD}{TerminalColors.RED}=== API-FEIL ==={TerminalColors.END}")
                print(f"Status: {response.status_code}")
                print(f"Svar: {response.text}")
            return None
            
    except Exception as e:
        if verbose:
            print(f"\n{TerminalColors.BOLD}{TerminalColors.RED}=== FEIL ==={TerminalColors.END}")
            print(f"Feil ved bruk av OpenAI API: {e}")
        return None 