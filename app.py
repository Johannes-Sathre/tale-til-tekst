import customtkinter as ctk  # Importerer customtkinter-biblioteket som ctk
import threading  # Importerer threading-biblioteket for å kjøre parallelle tråder
import os  # Importerer operativsystem-modulen for filsystemoperasjoner
from PIL import Image  # Importerer Image-klassen fra PIL-biblioteket for bildebehandling
from system_tray import SystemTrayIcon  # Importerer vår SystemTrayIcon-klasse
from app_gui import AppGUI  # Importerer vår AppGUI-klasse som viser brukergrensesnittet

class TaleTilTekstApp:  # Definerer hovedklassen for applikasjonen
    """
    Forenklet hovedklasse for applikasjonen.
    Koordinerer mellom GUI og system tray.
    """
    def __init__(self):  # Konstruktørmetode som kjøres når et objekt lages
        """
        Initialiserer applikasjonen.
        - Setter opp variabler
        - Oppretter system tray objekt
        """
        self.window = None  # Initialiserer window-attributtet til None
        self.system_tray = SystemTrayIcon(self)  # Oppretter et SystemTrayIcon-objekt med henvisning til denne klassen
    
    def create_window(self):  # Metode for å opprette hovedvinduet
        """
        Oppretter hovedvinduet for applikasjonen ved å instansiere AppGUI-klassen.
        """
        self.window = AppGUI(app_controller=self)  # Oppretter et AppGUI-objekt med henvisning til denne klassen som kontroller
    
    def show_window(self):  # Metode for å vise vinduet
        """
        Viser hovedvinduet og bringer det til forgrunnen.
        Kalles når brukeren klikker på "Vis app" i system tray-menyen.
        """
        if self.window:  # Sjekker om window-objektet eksisterer
            self.window.show()  # Kaller show-metoden på window-objektet for å vise det
    
    def hide_window(self):  # Metode for å skjule vinduet
        """
        Skjuler hovedvinduet i stedet for å avslutte.
        Kalles når brukeren klikker på X i tittellinjen.
        Appen fortsetter å kjøre i system tray.
        """
        if self.window:  # Sjekker om window-objektet eksisterer
            self.window.withdraw()  # Kaller withdraw-metoden på window-objektet for å skjule det
    
    def exit_app(self):  # Metode for å avslutte applikasjonen
        """
        Avslutter applikasjonen fullstendig.
        Kalles når brukeren velger "Avslutt" fra system tray-menyen.
        """
        if self.window:  # Sjekker om window-objektet eksisterer
            self.window.destroy()  # Kaller destroy-metoden på window-objektet for å lukke vinduet
    
    def start(self):  # Metode for å starte applikasjonen
        """
        Starter applikasjonen:
        1. Kjører system tray i egen tråd
        2. Oppretter hovedvinduet via AppGUI-klassen
        3. Starter hovedløkken (mainloop)
        """
        self.system_tray.run()  # Starter system tray-ikonet
        
        self.create_window()  # Oppretter hovedvinduet
        
        self.window.mainloop()  # Starter hovedløkken for GUI-et

if __name__ == "__main__":  # Sjekker om denne filen kjøres direkte (ikke importeres)
    ctk.set_appearance_mode("System")  # Setter utseendemodus for customtkinter
    ctk.set_default_color_theme("blue")  # Setter standard fargetema for customtkinter
    
    app = TaleTilTekstApp()  # Oppretter en instans av TaleTilTekstApp-klassen
    app.start()  # Kaller start-metoden for å starte applikasjonen
