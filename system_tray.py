import threading  # Importerer threading-biblioteket for å kjøre ikontråden parallelt
import pystray  # Importerer pystray-biblioteket for å lage systemstatusfeltikonet
from pystray import MenuItem as item  # Importerer MenuItem-klassen fra pystray og gir den navnet 'item'
from PIL import Image  # Importerer Image-klassen fra PIL-biblioteket for å håndtere ikonbilde

class SystemTrayIcon:  # Definerer SystemTrayIcon-klassen
    """
    Klasse for å håndtere system tray-ikonet i applikasjonen.
    System tray er ikonet som vises i Windows' statusfelt nederst til høyre.
    """
    def __init__(self, app_instance):  # Konstruktørmetode som kjøres når et objekt lages
        """
        Initialiserer SystemTrayIcon med referanse til hovedapplikasjonen.
        
        Args:
            app_instance: Referanse til hovedapplikasjonen (TaleTilTekstApp)
        """
        self.app_instance = app_instance  # Lagrer referanse til hovedappen
        self.icon = None  # Selve ikonet initialiseres senere

    def create_image(self):  # Metode for å laste inn ikonbilde
        """
        Laster inn ikonbildet fra ressursmappen.
        
        Returns:
            PIL.Image: Bildeobjektet for ikonet
        """
        return Image.open("resources/icon.png")  # Laster ikonbilde fra resources-mappen

    def setup_icon(self):  # Metode for å sette opp og kjøre ikonet
        """
        Setter opp system tray-ikonet med meny og handlinger.
        Denne kjører i egen tråd og blokkerer til ikonet stoppes.
        """
        # Oppretter menyen med to valg: Vis app og Avslutt
        menu = pystray.Menu(  # Lager en meny for ikonet
            item('Vis app', self.on_show_app, default=True),  # Legger til 'Vis app'-valg som er standard ved dobbelklikk
            item('Avslutt', self.on_exit)  # Legger til 'Avslutt'-valg i menyen
        )
        # Oppretter selve ikonet med navn, bilde, tooltip og meny
        self.icon = pystray.Icon("TaleTilTekst", self.create_image(), "Tale til Tekst", menu)  # Oppretter ikonobjektet
        self.icon.run()  # Starter ikonet - denne blokkerer til icon.stop() kalles

    def on_show_app(self, icon, item):  # Metode som kalles når 'Vis app'-valget klikkes
        """
        Kalles når brukeren klikker 'Vis app' i menyen.
        Viser hovedvinduet.
        
        Args:
            icon: Ikonobjektet
            item: Menyelementet som ble klikket
        """
        self.app_instance.show_window()  # Kaller show_window-metoden i hovedappen

    def on_exit(self, icon, item):  # Metode som kalles når 'Avslutt'-valget klikkes
        """
        Kalles når brukeren klikker 'Avslutt' i menyen.
        Stopper ikonet og avslutter applikasjonen.
        
        Args:
            icon: Ikonobjektet
            item: Menyelementet som ble klikket
        """
        self.icon.stop()  # Stopper ikonet og frigjør tråden
        self.app_instance.exit_app()  # Kaller exit_app-metoden i hovedappen

    def run(self):  # Metode for å starte ikonet i egen tråd
        """
        Starter system tray-ikonet i en egen tråd.
        Dette gjør at hovedappen kan fortsette å kjøre samtidig.
        """
        threading.Thread(target=self.setup_icon, daemon=True).start()  # Starter ikonet i egen tråd som daemon
