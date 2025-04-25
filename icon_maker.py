#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tale til Tekst - Ikongenerator

Genererer ikoner for applikasjonen.
"""

import os
from PIL import Image, ImageDraw

def create_app_icon():
    """Lager et moderne applikasjon-ikon"""
    # Ikonstørrelser 
    sizes = [16, 32, 48, 64, 128, 256]
    icons = []
    
    # Farger
    bg_color = (0, 120, 212)  # Windows blå
    accent_color = (255, 255, 255)  # Hvit
    
    for size in sizes:
        # Opprett tom bilde med transparens
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Beregn størrelser
        padding = size // 10
        inner_size = size - (padding * 2)
        
        # Tegn avrundet rektangel (simulert med sirkel og rektangler)
        corner_radius = size // 5
        
        # Tegn hovedbakgrunn (avrundet rektangel)
        draw.rectangle(
            [(padding, padding + corner_radius), 
             (padding + inner_size, padding + inner_size - corner_radius)], 
            fill=bg_color
        )
        draw.rectangle(
            [(padding + corner_radius, padding), 
             (padding + inner_size - corner_radius, padding + inner_size)], 
            fill=bg_color
        )
        
        # Tegn hjørner
        draw.ellipse(
            [(padding, padding), 
             (padding + corner_radius * 2, padding + corner_radius * 2)], 
            fill=bg_color
        )
        draw.ellipse(
            [(padding + inner_size - corner_radius * 2, padding), 
             (padding + inner_size, padding + corner_radius * 2)], 
            fill=bg_color
        )
        draw.ellipse(
            [(padding, padding + inner_size - corner_radius * 2), 
             (padding + corner_radius * 2, padding + inner_size)], 
            fill=bg_color
        )
        draw.ellipse(
            [(padding + inner_size - corner_radius * 2, padding + inner_size - corner_radius * 2), 
             (padding + inner_size, padding + inner_size)], 
            fill=bg_color
        )
        
        # Tegn mikrofon-ikonet
        mic_width = size // 4
        mic_height = size // 2.5
        mic_x = (size - mic_width) // 2
        mic_y = (size - mic_height) // 2 - size // 10
        
        # Mikrofon-base (rundet rektangel)
        draw.rectangle(
            [(mic_x + mic_width//5, mic_y), 
             (mic_x + mic_width - mic_width//5, mic_y + mic_height * 0.7)], 
            fill=accent_color
        )
        draw.ellipse(
            [(mic_x, mic_y), 
             (mic_x + mic_width//2.5, mic_y + mic_width//2.5)], 
            fill=accent_color
        )
        draw.ellipse(
            [(mic_x + mic_width - mic_width//2.5, mic_y), 
             (mic_x + mic_width, mic_y + mic_width//2.5)], 
            fill=accent_color
        )
        
        # Mikrofon stativ
        stand_width = mic_width // 4
        stand_height = mic_height // 2
        stand_x = (size - stand_width) // 2
        stand_y = mic_y + mic_height * 0.6
        
        draw.rectangle(
            [(stand_x, stand_y), 
             (stand_x + stand_width, stand_y + stand_height)], 
            fill=accent_color
        )
        
        # Base (fot)
        base_width = mic_width * 1.2
        base_height = size // 15
        base_x = (size - base_width) // 2
        base_y = stand_y + stand_height
        
        draw.rectangle(
            [(base_x, base_y), 
             (base_x + base_width, base_y + base_height)], 
            fill=accent_color
        )
        
        # Lydbølger (halvsirkler)
        if size >= 48:  # Bare vis lydbølger på større ikoner
            wave_count = 3
            max_wave_size = inner_size * 0.8
            wave_start_x = (size - max_wave_size) // 2
            wave_y = size // 2
            
            for i in range(wave_count):
                wave_size = max_wave_size - (i * (max_wave_size / wave_count / 2))
                wave_thickness = max(1, size // 64)
                wave_x = (size - wave_size) // 2
                
                # Tegn bare høyre halvdel av lydbølgen
                draw.arc(
                    [(wave_x, wave_y - wave_size//2), 
                     (wave_x + wave_size, wave_y + wave_size//2)], 
                    start=270, end=90, 
                    fill=accent_color, width=wave_thickness
                )
        
        icons.append(img)
    
    # Lagre ikonene
    for size, img in zip(sizes, icons):
        img.save(f"icon_{size}.png")
    
    # Lag en Windows ico-fil
    icons[0].save("icon.ico", format="ICO", sizes=[(size, size) for size in sizes])
    
    # Lag en systemfelt-ikon (64x64)
    icons[3].save("tray_icon.png")
    
    print(f"Genererte ikoner: {len(sizes)} størrelser + ICO-fil")

if __name__ == "__main__":
    create_app_icon() 